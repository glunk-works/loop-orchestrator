"""MCP-backed adapters for the two issue verbs — orchestrator-side callables
that drop into the engine's `issue_filer` seam / `cli resume`'s reader seam
without either caller knowing whether it's talking to `gh` directly or
through the `issue` MCP server. Both `mcp_issue_filer` and `mcp_issue_reader`
are **factories**: each takes a provider (and an optional explicit `repo`)
and returns the seam-compatible callable — a symmetric shape on both the
write and read sides (R1; earlier revisions had the read side as a raw
2-arg function, not a drop-in factory, which is why the two seams are
described identically here).

Rich domain objects (`State`, `Question`) never cross the MCP boundary: the
title/body/label are rendered locally (via the existing pure
`render_question_issue`) before the `create_issue` verb is dispatched, and the
returned `IssueRef`/view JSON is parsed back on this side.

`default_issue_filer`/`default_issue_reader` are the runtime defaults now
that the issue path is proven end to end (Sprint 27 V3): they open a fresh
`issue` MCP provider per call and dispatch through it, replacing the classic
direct `gh` calls that used to be the default.
"""

import json
from collections.abc import Callable
from pathlib import Path

from loop_orchestrator.core.state import IssueRef, Question, State
from loop_orchestrator.tools.issue_io.github import render_question_issue

# `tools/mcp`, `tools/repo_io`, and `tools/worktree` are deliberately imported
# inside `default_issue_filer`/`default_issue_reader` (F7), not here: those
# are the only two callers that need them, and importing them at module scope
# meant importing `core/engine` (which imports this module for the write
# seam) transitively dragged in the whole MCP client stack at import time.


class IssueDestinationUnresolvedError(Exception):
    """`default_issue_filer` could not name a destination repo for the
    escalation issue — e.g. the origin CWD is not a GitHub repository.
    Raised instead of falling back to an unnamed (`repo=None`) destination,
    which would silently restore the R8 leak this default exists to
    prevent."""


def mcp_issue_filer(
    provider, *, repo: str | None = None
) -> Callable[[State, list[Question], str], IssueRef]:
    """An `issue_filer`-compatible callable that files the issue through an
    already-entered MCP `provider` (as returned by `build_issue_provider()`)
    instead of shelling `gh` directly. `repo` (owner/repo), when given, is
    forwarded as an explicit destination (R8)."""

    def _file(state: State, questions: list[Question], snapshot_path: str) -> IssueRef:
        title, body, label = render_question_issue(state, questions, snapshot_path)
        result = provider.execute(
            "create_issue", {"title": title, "body": body, "label": label, "repo": repo}
        )
        return IssueRef.model_validate_json(result)

    return _file


def mcp_issue_reader(provider, *, repo: str | None = None) -> Callable[[int], dict]:
    """A reader-seam-compatible factory (`Callable[[int], dict]`) that reads
    an issue through an already-entered MCP `provider` instead of shelling
    `gh` directly. `repo`, when given, is forwarded as an explicit
    destination (R8), mirroring `mcp_issue_filer`."""

    def _read(issue_number: int) -> dict:
        result = provider.execute("read_issue", {"issue_number": issue_number, "repo": repo})
        return json.loads(result)

    return _read


def default_issue_filer(
    state: State, questions: list[Question], snapshot_path: str, *, cwd: str | Path | None = None
) -> IssueRef:
    """The runtime default `issue_filer`: names the destination repo explicitly
    (R8) instead of letting `gh` infer it from whatever CWD it happens to run in.

    The destination defaults to `worktree.origin_cwd()` — the directory the
    orchestrator was launched from — NOT the process CWD, which by the time a
    stage escalates is the run's worktree, whose remote is loop-orchestrator itself.
    That distinction is the whole finding: escalation issues for managed repos
    were landing on the project repo. Defaulting here rather than making each
    caller pass `cwd` is deliberate — the first cut of this fix threaded it from
    `cli.py` only, and `runner.run_new`/`run_in_tree` (fresh runs, the trigger
    surface, `flows/maintenance`) silently kept leaking.

    `cwd` is an override for a caller that knows better. Resolution is lazy:
    the `gh repo view` costs nothing on a run that never escalates.
    """
    from loop_orchestrator.tools.mcp import build_issue_provider
    from loop_orchestrator.tools.repo_io import RepoNotResolvableError, resolve_repo_slug
    from loop_orchestrator.tools.worktree import origin_cwd

    origin = cwd if cwd is not None else origin_cwd()
    try:
        repo = resolve_repo_slug(origin)
    except RepoNotResolvableError as exc:
        # F4: make the failure legible instead of a raw resolve_repo_slug
        # error surfacing from inside the pause path — and do NOT fall back
        # to repo=None, which would silently restore the R8 leak.
        raise IssueDestinationUnresolvedError(
            f"Could not resolve a destination repo for the escalation issue: {exc} "
            "Refusing to file without an explicit destination."
        ) from exc
    with build_issue_provider() as provider:
        return mcp_issue_filer(provider, repo=repo)(state, questions, snapshot_path)


def default_issue_reader(issue_number: int, *, repo: str | None = None) -> dict:
    """The runtime default issue reader, mirroring `default_issue_filer`.

    `repo` (owner/repo) names the repo to read the issue *from*. It cannot be
    defaulted the way the filer's can: on `resume --from-issue N` the snapshot
    is not loaded yet (its path comes out of the issue body), so the run's own
    repo is not yet knowable — hence `cli.resume`'s `--repo` option. Left
    unset, `cli.resume` resolves and echoes an explicit repo before calling
    this (F1b: never `gh`'s implicit CWD resolution) -- `resume --snapshot`
    instead derives the repo from the snapshot's own `pending_issue.url`
    (F1a), which is unambiguous and never reaches this default's own `repo`
    argument as `None`.
    """
    from loop_orchestrator.tools.mcp import build_issue_provider

    with build_issue_provider() as provider:
        return mcp_issue_reader(provider, repo=repo)(issue_number)
