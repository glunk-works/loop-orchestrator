"""GitHub repository factory verbs — the second `gh`-shelling module.

Sibling to `tools/issue_io`: together they are the codebase's GitHub-owning
modules (`issue_io` = human-escalation verbs, `repo_io` = repo/branch/PR
factory verbs). Mirrors `issue_io.github`'s transport shape exactly — shells
out to the already-authenticated `gh` executable rather than embedding a
token, so no credential ever passes through this process's own
configuration. `repo_io` imports no `keyring` and writes no files (`gh repo
clone`'s destination is `gh`'s own I/O, not a `state_io`-guarded write).

These four verbs (`create_repository`, `clone_repo`, `create_branch`,
`open_pr`) are orchestrator-invoked factory operations, never model tools —
see `tools/mcp/provider.py::build_github_provider` for the consumer-scoped
boundary that keeps them out of the agentic Coder's tool loop. Deliberately
no merge verb: auto-merge is prohibited.
"""

import subprocess
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field


class RepoRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    url: str


class PullRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    url: str


def _run_gh(args: list[str]) -> str:
    result = subprocess.run(  # noqa: S603 -- fixed executable, no shell, args are not attacker-controlled strings
        ["gh", *args],  # noqa: S607 -- resolved via PATH intentionally: gh's install location varies by platform
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return result.stdout


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
