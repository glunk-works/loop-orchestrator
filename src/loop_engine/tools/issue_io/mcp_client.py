"""MCP-backed adapters for the two issue verbs — orchestrator-side callables
signature-compatible with the classic `file_question_issue`/`read_issue`, so
they drop into the engine's `issue_filer` seam / `cli resume`'s reader seam
without either caller knowing whether it's talking to `gh` directly or
through the `issue` MCP server.

Rich domain objects (`State`, `Question`) never cross the MCP boundary: the
title/body/label are rendered locally (via the existing pure
`render_question_issue`) before the `create_issue` verb is dispatched, and the
returned `IssueRef`/view JSON is parsed back on this side.
"""

import json
from collections.abc import Callable

from loop_engine.core.state import IssueRef, Question, State
from loop_engine.tools.issue_io.github import render_question_issue


def mcp_issue_filer(
    provider,
) -> Callable[[State, list[Question], str], IssueRef]:
    """An `issue_filer`-compatible callable that files the issue through an
    already-entered MCP `provider` (as returned by `build_issue_provider()`)
    instead of shelling `gh` directly."""

    def _file(state: State, questions: list[Question], snapshot_path: str) -> IssueRef:
        title, body, label = render_question_issue(state, questions, snapshot_path)
        result = provider.execute("create_issue", {"title": title, "body": body, "label": label})
        return IssueRef.model_validate_json(result)

    return _file


def mcp_read_issue(provider, issue_number: int) -> dict:
    """A `read_issue`-compatible call that reads the issue through an
    already-entered MCP `provider` instead of shelling `gh` directly."""
    result = provider.execute("read_issue", {"issue_number": issue_number})
    return json.loads(result)
