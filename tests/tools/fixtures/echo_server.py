"""Trivial stdio MCP server fixture: one `ping` tool. Used to prove
`MCPToolProvider` discovers and routes to more than one server (sprint 22a,
Task 3) without conflating the test with the coder-tools server's own tool
set. Run as: `python -m tests.tools.fixtures.echo_server`.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("loop-engine-test-echo")


@mcp.tool()
def ping(message: str) -> str:
    """Echo the message back with an 'echo:' prefix."""
    return f"echo:{message}"


if __name__ == "__main__":
    mcp.run()
