"""MCP client layer: dynamic tool discovery and dispatch for the LLM tool loop.

`MCPToolProvider` connects to one or more stdio MCP servers, discovers their
tools at runtime (`list_tools`), and exposes them to the synchronous tool loop
as (a) Anthropic-format tool schemas and (b) a `execute(name, args)` callback
that routes each call to the owning server. This replaces the in-process
`if/elif` dispatch when LOOP_ENGINE_TOOLS=mcp is set.
"""

from loop_engine.tools.mcp.provider import (
    MCPToolError,
    MCPToolProvider,
    build_coder_tool_provider,
    use_mcp_tools,
)

__all__ = [
    "MCPToolError",
    "MCPToolProvider",
    "build_coder_tool_provider",
    "use_mcp_tools",
]
