"""MCP client layer: dynamic tool discovery and dispatch for the LLM tool loop.

`MCPToolProvider` connects to one or more stdio MCP servers, discovers their
tools at runtime (`list_tools`), and exposes them to the synchronous tool loop
as (a) Anthropic-format tool schemas and (b) a `execute(name, args)` callback
that routes each call to the owning server. This replaces the in-process
`if/elif` dispatch when LOOP_ENGINE_TOOLS=mcp is set.
"""

from loop_engine.tools.mcp.config import (
    CODER_TOOLS_SERVER_NAME,
    MCPServerSpec,
    load_mcp_config,
)
from loop_engine.tools.mcp.provider import (
    MCPToolError,
    MCPToolProvider,
    build_coder_tool_provider,
    build_provider_for,
    coder_tools_server_params,
    container_server_params,
    sandbox_server_params,
    use_mcp_tools,
)

__all__ = [
    "CODER_TOOLS_SERVER_NAME",
    "MCPServerSpec",
    "MCPToolError",
    "MCPToolProvider",
    "build_coder_tool_provider",
    "build_provider_for",
    "coder_tools_server_params",
    "container_server_params",
    "load_mcp_config",
    "sandbox_server_params",
    "use_mcp_tools",
]
