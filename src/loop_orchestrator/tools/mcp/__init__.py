"""MCP client layer: dynamic tool discovery and dispatch for the LLM tool loop.

`MCPToolProvider` connects to one or more stdio MCP servers, discovers their
tools at runtime (`list_tools`), and exposes them to the synchronous tool loop
as (a) Anthropic-format tool schemas and (b) a `execute(name, args)` callback
that routes each call to the owning server. This replaces the in-process
`if/elif` dispatch, which Phase 6 deleted.
"""

from loop_orchestrator.tools.mcp.config import (
    CODER_TOOLS_SERVER_NAME,
    GITHUB_SERVER_NAME,
    ISSUE_SERVER_NAME,
    MCPServerSpec,
    load_mcp_config,
)
from loop_orchestrator.tools.mcp.provider import (
    MCPToolError,
    MCPToolProvider,
    build_coder_tool_provider,
    build_github_provider,
    build_issue_provider,
    build_provider_for,
    container_server_params,
    run_gate_pytest,
    sandbox_server_params,
)

__all__ = [
    "CODER_TOOLS_SERVER_NAME",
    "GITHUB_SERVER_NAME",
    "ISSUE_SERVER_NAME",
    "MCPServerSpec",
    "MCPToolError",
    "MCPToolProvider",
    "build_coder_tool_provider",
    "build_github_provider",
    "build_issue_provider",
    "build_provider_for",
    "container_server_params",
    "load_mcp_config",
    "run_gate_pytest",
    "sandbox_server_params",
]
