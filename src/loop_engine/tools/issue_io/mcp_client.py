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

from loop_engine.core.state import IssueRef, Question, State
from loop_engine.tools.issue_io.github import render_question_issue, resolve_repo_slug
from loop_engine.tools.mcp import build_issue_provider


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
    state: State, questions: list[Question], snapshot_path: str, *, cwd: str | None = None
) -> IssueRef:
    """The runtime default `issue_filer`. Resolves the destination repo
    lazily — only if an issue is actually filed — from `cwd`: pass the
    caller's cwd captured *before* any worktree chdir (R8), so an escalation
    raised from deep inside a run's worktree still targets the repo the
    orchestrator was launched against, not wherever `gh`'s own implicit
    cwd-based resolution would land inside the worktree. `cwd=None` (the
    default when a caller hasn't captured one) falls back to `gh`'s implicit
    resolution, matching the classic path's pre-existing behavior."""
    repo = resolve_repo_slug(cwd) if cwd is not None else None
    with build_issue_provider() as provider:
        return mcp_issue_filer(provider, repo=repo)(state, questions, snapshot_path)


def default_issue_reader(issue_number: int) -> dict:
    """The runtime default issue reader, mirroring `default_issue_filer`."""
    with build_issue_provider() as provider:
        return mcp_issue_reader(provider)(issue_number)
