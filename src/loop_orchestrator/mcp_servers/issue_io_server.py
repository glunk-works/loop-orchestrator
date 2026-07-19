"""Human-escalation GitHub Issue verbs as a stdio MCP server.

Native re-front (mirrors `github_server.py`'s shape) of the two `tools/issue_io`
`gh`-touching primitives — `create_issue`, `read_issue`. `issue_io` itself does
the `gh` shelling (already one of the four sanctioned subprocess surfaces);
this module holds no credentials and makes no `gh` call at import time, so
discovery (`list_tools`) stays offline/hermetic.

These verbs are **orchestrator-invoked, never a model tool**: they are
reached only through `tools/mcp/provider.py::build_issue_provider`, a
consumer-scoped provider distinct from `build_coder_tool_provider` — the
agentic Coder's tool loop never names this server. String/JSON-in,
string/JSON-out only: `State`/`Question` never cross this boundary — rendering
and parsing stay pure lib in `tools/issue_io`.

Run as: `python -m loop_orchestrator.mcp_servers.issue_io_server`
"""

import json

from mcp.server.fastmcp import FastMCP

from loop_orchestrator.tools.issue_io import create_issue as _create_issue
from loop_orchestrator.tools.issue_io import read_issue as _read_issue

mcp = FastMCP("loop-orchestrator-issue")


@mcp.tool()
def create_issue(title: str, body: str, label: str, repo: str | None = None) -> str:
    """File a human-escalation GitHub Issue via `gh issue create`.
    Orchestrator-only. `repo` (owner/repo), when given, targets that repo
    explicitly instead of `gh`'s implicit cwd-derived resolution. Returns
    the created issue's number and URL as JSON."""
    return _create_issue(title, body, label, repo=repo).model_dump_json()


@mcp.tool()
def read_issue(issue_number: int, repo: str | None = None) -> str:
    """Read a GitHub Issue's state/body/comments via `gh issue view`.
    Orchestrator-only. `repo`, when given, targets that repo explicitly.
    Returns the raw `gh` JSON view."""
    return json.dumps(_read_issue(issue_number, repo=repo))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
