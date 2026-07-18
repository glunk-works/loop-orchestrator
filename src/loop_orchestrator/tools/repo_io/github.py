"""GitHub repository factory verbs — the second `gh`-shelling module.

Sibling to `tools/issue_io`: together they are the codebase's GitHub-owning
modules (`issue_io` = human-escalation verbs, `repo_io` = repo/branch/PR
factory verbs). Mirrors `issue_io.github`'s transport shape exactly — shells
out to the already-authenticated `gh` executable rather than embedding a
token, so no credential ever passes through this process's own
configuration. `repo_io` imports no `keyring` and writes no files (`gh repo
clone`'s destination is `gh`'s own I/O, not a `state_io`-guarded write).

These five verbs (`create_repository`, `clone_repo`, `create_branch`,
`open_pr`, `create_ruleset`) are orchestrator-invoked factory operations,
never model tools — see `tools/mcp/provider.py::build_github_provider` for
the consumer-scoped boundary that keeps them out of the agentic Coder's tool
loop. Deliberately no merge verb: auto-merge is prohibited. `create_ruleset`
(sprint 36, BL-21) is deliberately **not** a sixth MCP verb — it follows
`resolve_repo_slug`'s precedent of orchestrator-only introspection/admin
verbs that never enter `mcp_servers/github_server`, which stays pinned at
exactly four.
"""

import json
import subprocess
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field


class RepoNotResolvableError(Exception):
    """`resolve_repo_slug` could not determine the repo `cwd` belongs to --
    e.g. `cwd` is not inside a GitHub repository. Raised instead of letting a
    raw `subprocess.CalledProcessError` cross this module's boundary, so a
    caller (F4: `tools/issue_io`'s `default_issue_filer`) can catch it
    without itself importing `subprocess` -- `repo_io` stays the only owner
    of that surface."""


class RulesetInstallError(Exception):
    """`create_ruleset`'s underlying `gh` call exited non-zero -- i.e.
    `_run_gh` raised `subprocess.CalledProcessError` -- so the GitHub API
    DEFINITIVELY rejected the ruleset POST and it genuinely was NOT created
    (S5, sprint 36 review; narrowed from `SubprocessError` in round 4). The
    message carries `gh`'s stderr (the 403/422 body) so a caller can surface
    *why* it was rejected -- `str(CalledProcessError)` alone is just "Command
    ... returned non-zero exit status N" and drops the status code. Raised
    instead of letting the raw subprocess error cross this module's boundary,
    mirroring `RepoNotResolvableError`: `flows/bootstrap.run_bootstrap` catches
    this without itself importing `subprocess` (`flows/` adds no subprocess
    surface of its own -- `tests/flows/test_boundaries.py`).

    Deliberately NOT raised for the two *ambiguous* failure modes where the
    ruleset may already exist -- wrapping either would let an operator tear
    down a *protected* repo: a `TimeoutExpired` (the POST may have applied
    server-side, the client just never saw the response) and a *successful*
    POST that returns an unparseable body (`json.loads(...)["id"]` raising
    `JSONDecodeError`/`KeyError`). Both propagate unwrapped."""


class RepoRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    url: str


class PullRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    url: str


def _run_gh(
    args: list[str], *, cwd: str | Path | None = None, input_data: str | None = None
) -> str:
    result = subprocess.run(  # noqa: S603 -- fixed executable, no shell, args are not attacker-controlled strings
        ["gh", *args],  # noqa: S607 -- resolved via PATH intentionally: gh's install location varies by platform
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
        cwd=cwd,
        input=input_data,
    )
    return result.stdout


def resolve_repo_slug(cwd: str | Path | None = None) -> str:
    """The `owner/repo` slug of the GitHub repo `cwd` belongs to.

    Repo *introspection*, so it lives here rather than in `issue_io` (whose
    charter is filing/reading escalation issues) — but its motivating caller is
    the issue filer. `gh` otherwise derives an issue's destination from its own
    ambient CWD; naming the destination explicitly is what finding R8 asked for,
    and that name has to come from somewhere. Resolve it against a CWD you have
    deliberately chosen (the orchestrator's origin — see `worktree.origin_cwd`),
    not one you inherited.
    """
    args = ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
    try:
        return _run_gh(args, cwd=cwd).strip()
    except subprocess.CalledProcessError as exc:
        raise RepoNotResolvableError(
            f"{cwd} is not a GitHub repository (`gh repo view` failed): {exc}"
        ) from exc


def _validate_clone_dest(dest: str) -> Path:
    """Validate a `clone_repo` destination: relative, no traversal, no
    symlink escape out of the run tree. Mirrors the discipline
    `tools/coder_tools.resolve_tool_path` applies to model-supplied paths
    (itself built on `tools/state_io`'s traversal rules), minus the
    artifact-root allowlist — a clone destination is not confined to
    docs/sprints/src."""
    normalized = dest.replace("\\", "/")
    if not normalized or normalized.startswith("/"):
        raise ValueError(f"Invalid clone destination: {dest!r} must be a relative path")

    posix_path = PurePosixPath(normalized)
    parts = posix_path.parts
    if not parts or ".." in parts:
        raise ValueError(f"Invalid clone destination: {dest!r} must not contain '..' segments")

    path = Path(*parts)
    # Resolve unconditionally (not gated on `path.exists()`): a clone target
    # normally does NOT exist yet, and `Path.resolve()` still resolves any
    # symlinked *prefix* for a non-existent tail — so a symlinked parent
    # (`link/repo` where `link -> /outside`) must be caught here, not skipped.
    if not path.resolve().is_relative_to(Path.cwd().resolve()):
        raise ValueError(f"Invalid clone destination: {dest!r} escapes the run tree")
    return path


def create_repository(name: str, *, org: str | None = None, private: bool = True) -> RepoRef:
    slug = f"{org}/{name}" if org else name
    visibility_flag = "--private" if private else "--public"
    url = _run_gh(["repo", "create", slug, visibility_flag]).strip()
    repo_slug = "/".join(url.rstrip("/").split("/")[-2:])
    return RepoRef(slug=repo_slug, url=url)


def clone_repo(slug: str, dest: str, *, depth: int | None = None) -> str:
    dest_path = _validate_clone_dest(dest)
    args = ["repo", "clone", slug, str(dest_path)]
    if depth is not None:
        args += ["--", "--depth", str(depth)]
    _run_gh(args)
    return str(dest_path)


def _default_branch(owner: str, repo: str) -> str:
    return _run_gh(["api", f"repos/{owner}/{repo}", "--jq", ".default_branch"]).strip()


def create_branch(owner: str, repo: str, branch: str, *, base: str | None = None) -> str:
    base_branch = base if base is not None else _default_branch(owner, repo)
    sha = _run_gh(
        ["api", f"repos/{owner}/{repo}/git/ref/heads/{base_branch}", "--jq", ".object.sha"]
    ).strip()
    ref = f"refs/heads/{branch}"
    _run_gh(
        [
            "api",
            "--method",
            "POST",
            f"repos/{owner}/{repo}/git/refs",
            "-f",
            f"ref={ref}",
            "-f",
            f"sha={sha}",
        ]
    )
    return ref


def open_pr(owner: str, repo: str, *, head: str, base: str, title: str, body: str) -> PullRef:
    url = _run_gh(
        [
            "pr",
            "create",
            "--repo",
            f"{owner}/{repo}",
            "--head",
            head,
            "--base",
            base,
            "--title",
            title,
            "--body",
            body,
        ]
    ).strip()
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    return PullRef(number=number, url=url)


def create_ruleset(
    owner: str,
    repo: str,
    *,
    branches: list[str],
    name: str = "protect-integration-branches",
) -> int:
    """Install a repository ruleset protecting `branches` -- BL-21's fix.
    Targets **every** branch in `branches` (FD5: a generated repo's PRs land
    on `develop`, not `main`, via `flows/maintenance`'s `base="develop"`, so
    protecting `main` alone would gate a door nobody uses). Ships exactly
    `deletion` + `non_fast_forward` + `pull_request`, and deliberately
    **no** `required_status_checks` rule (FD4 -- a factory-scaffolded repo
    ships no CI workflow at all; a required check that can never report
    would permanently deadlock the repo's merges). `enforcement="active"`,
    no bypass actors.

    Orchestrator-only (FD6), following `resolve_repo_slug`'s precedent: this
    is a `repo_io` verb but never an MCP tool, so `mcp_servers/github_server`
    stays pinned at exactly four verbs.

    The ruleset POST body is non-trivial nested JSON, so it is built
    explicitly and piped through `gh api --input -` rather than hand-spliced
    as `-f` flags (which cannot express nested arrays/objects).
    """
    if not branches:
        raise ValueError("create_ruleset requires at least one branch in `branches`")

    body = {
        "name": name,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {
                "include": [f"refs/heads/{branch}" for branch in branches],
                "exclude": [],
            }
        },
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": False,
                },
            },
        ],
    }
    try:
        output = _run_gh(
            ["api", "--method", "POST", f"repos/{owner}/{repo}/rulesets", "--input", "-"],
            input_data=json.dumps(body),
        )
    except subprocess.CalledProcessError as exc:
        # S5 + sprint-36 round-4 review (findings 1-2): `gh` exited non-zero,
        # so the API DEFINITIVELY rejected the POST -- the ruleset genuinely
        # was not created. Carry `gh`'s stderr (the 403/422 body) into the
        # message rather than only `str(exc)` (which is just "Command ...
        # returned non-zero exit status N" and drops the status code an
        # operator needs). Wrapped so a caller (`flows/bootstrap`) can catch
        # it without importing `subprocess` -- mirrors `RepoNotResolvableError`.
        detail = exc.stderr.strip() if isinstance(exc.stderr, str) and exc.stderr.strip() else ""
        raise RulesetInstallError(f"{exc}: {detail}" if detail else str(exc)) from exc
    # Two failure modes are DELIBERATELY left unwrapped, because both mean the
    # ruleset may already exist -- so mislabeling them RULESET_FAILED would tell
    # an operator a *protected* repo is safe to tear down:
    #   * a `TimeoutExpired` (the POST may have applied server-side; the client
    #     just never saw the response) -- hence `CalledProcessError` above, not
    #     the broader `SubprocessError`;
    #   * a successful POST whose body is unparseable (`json.JSONDecodeError`/
    #     `KeyError` below).
    return json.loads(output)["id"]
