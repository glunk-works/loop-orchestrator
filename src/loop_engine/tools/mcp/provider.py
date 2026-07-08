"""Synchronous facade over async MCP client sessions.

The tool loop (`LLMClient.run_tool_loop`) is synchronous and calls its
`execute` callback repeatedly for one turn. MCP client sessions are async and
must have their context managers entered and exited in the *same* task (an
anyio constraint). So a single long-lived "serve" coroutine on a background
event-loop thread opens the sessions, publishes the discovered tools, then
parks until shutdown — and `execute` submits `call_tool` coroutines onto that
same loop, blocking for the result. Nothing here imports keyring or writes files.
"""

import asyncio
import logging
import os
import sys
import threading
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

_TOOLS_ENV_VAR = "LOOP_ENGINE_TOOLS"
_MCP_VALUE = "mcp"

_CODER_TOOLS_SERVER_MODULE = "loop_engine.mcp_servers.coder_tools_server"

# Bounds so a hung server can never wedge the run indefinitely.
_CONNECT_TIMEOUT_S = 30.0
_CALL_TIMEOUT_S = 150.0
_SHUTDOWN_TIMEOUT_S = 10.0


class MCPToolError(Exception):
    """An MCP tool returned an error result. Raised from `execute` so the tool
    loop surfaces it to the model as an `is_error` result — exactly as it does
    for an in-process tool that raises."""


def use_mcp_tools() -> bool:
    """Whether MCP tool dispatch is selected via the environment flag."""
    return os.environ.get(_TOOLS_ENV_VAR, "").strip().lower() == _MCP_VALUE


def coder_tools_server_params(cwd: str | Path | None = None) -> StdioServerParameters:
    """Launch parameters for the coder-tools stdio server. The server runs its
    tools relative to its own cwd, so it inherits the run tree's directory."""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", _CODER_TOOLS_SERVER_MODULE],
        cwd=str(cwd) if cwd is not None else None,
    )


class MCPToolProvider:
    """Connects to stdio MCP servers, discovers their tools, and dispatches
    tool calls. Use as a context manager: connections open on enter and are
    torn down on exit."""

    def __init__(self, servers: list[StdioServerParameters]) -> None:
        self._servers = servers
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._sessions: dict[str, ClientSession] = {}
        self._tools: list[dict] = []
        self._shutdown: asyncio.Event | None = None
        self._serve_future: asyncio.Future | None = None
        self._ready = threading.Event()
        self._connect_error: BaseException | None = None

    @property
    def tools(self) -> list[dict]:
        """Discovered tools as Anthropic-format schema dicts."""
        return self._tools

    def __enter__(self) -> "MCPToolProvider":
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._serve_future = asyncio.run_coroutine_threadsafe(self._serve(), self._loop)
        if not self._ready.wait(timeout=_CONNECT_TIMEOUT_S):
            self.__exit__(None, None, None)
            raise TimeoutError("MCP server(s) did not become ready in time")
        if self._connect_error is not None:
            error = self._connect_error
            self.__exit__(None, None, None)
            raise error
        return self

    async def _serve(self) -> None:
        try:
            async with AsyncExitStack() as stack:
                for params in self._servers:
                    read, write = await stack.enter_async_context(stdio_client(params))
                    session = await stack.enter_async_context(ClientSession(read, write))
                    await session.initialize()
                    listed = await session.list_tools()
                    for tool in listed.tools:
                        self._tools.append(
                            {
                                "name": tool.name,
                                "description": tool.description or "",
                                "input_schema": tool.inputSchema,
                            }
                        )
                        self._sessions[tool.name] = session
                self._shutdown = asyncio.Event()
                self._ready.set()
                await self._shutdown.wait()
        except BaseException as exc:  # noqa: BLE001 — reported to the caller thread
            self._connect_error = exc
            self._ready.set()

    def execute(self, name: str, arguments: dict) -> str:
        """Route a tool call to the owning server and return its text output.

        Raises MCPToolError on an error result so the tool loop records an
        is_error result, matching the in-process dispatch contract.
        """
        session = self._sessions.get(name)
        if session is None or self._loop is None:
            raise MCPToolError(f"Unknown MCP tool: {name!r}")
        future = asyncio.run_coroutine_threadsafe(
            session.call_tool(name, arguments or {}), self._loop
        )
        result = future.result(timeout=_CALL_TIMEOUT_S)
        text = "".join(getattr(block, "text", "") for block in result.content)
        if result.isError:
            raise MCPToolError(text or f"MCP tool {name!r} failed")
        return text

    def __exit__(self, *exc_info) -> None:
        if self._loop is not None and self._shutdown is not None:
            self._loop.call_soon_threadsafe(self._shutdown.set)
        if self._serve_future is not None:
            try:
                self._serve_future.result(timeout=_SHUTDOWN_TIMEOUT_S)
            except Exception as exc:  # noqa: BLE001 — teardown is best-effort
                logger.debug("MCP provider serve task raised during shutdown: %s", exc)
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread is not None:
                self._thread.join(timeout=_SHUTDOWN_TIMEOUT_S)
            self._loop.close()
            self._loop = None


def build_coder_tool_provider(cwd: str | Path | None = None) -> MCPToolProvider:
    """A provider wired to the coder-tools stdio server (the runtime tool set
    the agentic Coder uses)."""
    return MCPToolProvider([coder_tools_server_params(cwd)])
