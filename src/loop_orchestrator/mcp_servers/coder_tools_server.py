"""Coder tools as a stdio MCP server.

Exposes the agentic Coder's read/execute tool set — `read_file`, `list_files`,
`grep`, `run_tests`, `run_lint` — over MCP by delegating to the existing
in-process implementations in `tools/coder_tools`. Every path stays subject
to the same traversal/symlink validation (the delegated functions enforce
it), and the server holds no credentials. Tools operate relative to the
server process's working directory, so the client launches it with cwd set
to the run tree.

Run as: `python -m loop_orchestrator.mcp_servers.coder_tools_server`
"""

from mcp.server.fastmcp import FastMCP

from loop_orchestrator.tools.coder_tools import grep as _grep
from loop_orchestrator.tools.coder_tools import list_files as _list_files
from loop_orchestrator.tools.coder_tools import read_file as _read_file
from loop_orchestrator.tools.coder_tools.run_lint import run_lint as _run_lint
from loop_orchestrator.tools.coder_tools.run_tests import run_tests as _run_tests

mcp = FastMCP("loop-orchestrator-coder-tools")


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the run's artifact tree (docs/, sprints/, src/). Use it
    to inspect prior sprints' outputs before building on them."""
    return _read_file(path)


@mcp.tool()
def list_files(path: str) -> str:
    """Recursively list files under a directory in the run's artifact tree
    (docs/, sprints/, src/)."""
    return _list_files(path)


@mcp.tool()
def grep(pattern: str, path: str) -> str:
    """Search file contents under the run's artifact tree with a regular
    expression; returns path:line:text matches."""
    return _grep(pattern, path)


@mcp.tool()
def run_tests(path: str) -> str:
    """Run pytest against a file or directory in the run's artifact tree (e.g.
    src/). Use it to verify your implementation before claiming any acceptance
    criterion is met."""
    return _run_tests(path)


@mcp.tool()
def run_lint(path: str) -> str:
    """Run `ruff check` and `ruff format --check` against a file or directory
    in the run's artifact tree (e.g. src/). Use it to verify your
    implementation before claiming any 'ruff clean' acceptance criterion is
    met."""
    return _run_lint(path)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
