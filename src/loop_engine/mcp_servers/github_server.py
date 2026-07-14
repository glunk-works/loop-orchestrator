"""GitHub repository factory verbs as a stdio MCP server.

Native re-front (mirrors `coder_tools_server.py`'s shape) of the four
`tools/repo_io` factory verbs — `create_repository`, `clone_repo`,
`create_branch`, `open_pr` — over MCP. `repo_io` itself does the `gh`
shelling; this module holds no credentials and makes no `gh` call at import
time, so discovery (`list_tools`) stays offline/hermetic.

These verbs are **orchestrator-invoked, never a model tool**: they are
reached only through `tools/mcp/provider.py::build_github_provider`, a
consumer-scoped provider distinct from `build_coder_tool_provider` — the
agentic Coder's tool loop never names this server. Deliberately no merge
verb: auto-merge is prohibited.

Run as: `python -m loop_engine.mcp_servers.github_server`
"""

from mcp.server.fastmcp import FastMCP

from loop_engine.tools.repo_io import clone_repo as _clone_repo
from loop_engine.tools.repo_io import create_branch as _create_branch
from loop_engine.tools.repo_io import create_repository as _create_repository
from loop_engine.tools.repo_io import open_pr as _open_pr

mcp = FastMCP("loop-engine-github")


@mcp.tool()
def create_repository(name: str, org: str | None = None, private: bool = True) -> str:
    """Create a new GitHub repository via `gh repo create`. Orchestrator-only —
    a factory verb for bootstrap flows, never invoked by the model. Returns
    the created repo's slug and URL as JSON."""
    return _create_repository(name, org=org, private=private).model_dump_json()


@mcp.tool()
def clone_repo(slug: str, dest: str, depth: int | None = None) -> str:
    """Clone a GitHub repository via `gh repo clone` to a validated
    destination inside the run tree. Orchestrator-only. Returns the clone
    path."""
    return _clone_repo(slug, dest, depth=depth)


@mcp.tool()
def create_branch(owner: str, repo: str, branch: str, base: str | None = None) -> str:
    """Create a new remote branch (ref) on a GitHub repository, based on
    `base` or the repo's default branch. Orchestrator-only. Returns the
    created ref (e.g. `refs/heads/<branch>`)."""
    return _create_branch(owner, repo, branch, base=base)


@mcp.tool()
def open_pr(owner: str, repo: str, head: str, base: str, title: str, body: str) -> str:
    """Open a pull request via `gh pr create`. Orchestrator-only — no merge
    verb exists alongside it; auto-merge is prohibited. Returns the created
    PR's number and URL as JSON."""
    return _open_pr(owner, repo, head=head, base=base, title=title, body=body).model_dump_json()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
