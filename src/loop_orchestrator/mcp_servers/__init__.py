"""Standalone MCP servers that re-front loop-orchestrator's native tools.

Each server is a thin stdio wrapper over an existing in-process implementation
in `tools/` — the logic is not rewritten, only exposed over the Model Context
Protocol so tool execution runs out-of-process from the orchestrator. The LLM
client discovers and dispatches to these via `tools/mcp` behind the
MCP tool path — since Phase 6, the only tool path.
"""
