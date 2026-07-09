"""Trivial stdio MCP server fixture: one `greet` tool. Paired with
`echo_server` to prove `MCPToolProvider` routes each call to the correct
server among several (sprint 22a, Task 3). Run as:
`python -m tests.tools.fixtures.greet_server`.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("loop-engine-test-greet")


@mcp.tool()
def greet(name: str) -> str:
    """Greet the given name."""
    return f"hello, {name}"


if __name__ == "__main__":
    mcp.run()
