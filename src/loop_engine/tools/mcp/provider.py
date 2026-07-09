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
import shutil
import sys
import threading
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from loop_engine.tools.isolation import IsolationUnavailableError, sandbox_runtime_mode
from loop_engine.tools.mcp.config import (
    CODER_TOOLS_SERVER_NAME,
    MCPServerSpec,
    load_mcp_config,
)

logger = logging.getLogger(__name__)

_TOOLS_ENV_VAR = "LOOP_ENGINE_TOOLS"
_MCP_VALUE = "mcp"

_CODER_TOOLS_SERVER_MODULE = "loop_engine.mcp_servers.coder_tools_server"

# Phase 3b sandbox launch (env-overridable): the container runtime, the dev-stage
# image tag, and the uid:gid the sandbox runs as (defaults to the orchestrator's
# own, so bind-mounted artifacts keep correct host ownership).
_CONTAINER_RUNTIME_ENV_VAR = "LOOP_ENGINE_CONTAINER_RUNTIME"
_DEV_IMAGE_ENV_VAR = "LOOP_ENGINE_DEV_IMAGE"
_SANDBOX_UID_ENV_VAR = "LOOP_ENGINE_SANDBOX_UID"
_SUPPORTED_RUNTIMES = ("docker", "podman")

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


def _container_runtime() -> str:
    """Resolve the container runtime (`docker`/`podman`). An explicit
    `LOOP_ENGINE_CONTAINER_RUNTIME` override wins; otherwise the first one found
    on PATH. Raises `IsolationUnavailableError` when none is available — the
    caller must never fall back to in-process execution.

    Uses `shutil.which` (a PATH lookup), not a subprocess: this module adds no
    new sanctioned subprocess surface — the runtime is spawned by the MCP stdio
    client, exactly as the in-process server is."""
    override = os.environ.get(_CONTAINER_RUNTIME_ENV_VAR, "").strip().lower()
    if override:
        if override not in _SUPPORTED_RUNTIMES:
            raise IsolationUnavailableError(
                f"{_CONTAINER_RUNTIME_ENV_VAR}={override!r} is not supported "
                f"(expected one of {_SUPPORTED_RUNTIMES})"
            )
        if shutil.which(override) is None:
            raise IsolationUnavailableError(
                f"container isolation selected but {override!r} is not on PATH"
            )
        return override
    for runtime in _SUPPORTED_RUNTIMES:
        if shutil.which(runtime) is not None:
            return runtime
    raise IsolationUnavailableError(
        "container isolation selected but no container runtime (docker/podman) is "
        "on PATH; refusing to run untrusted code in-process"
    )


def _sandbox_user() -> str:
    """The `uid:gid` the sandbox runs as. Defaults to the orchestrator's own so
    files the sandbox writes into the bind-mounted worktree stay host-owned."""
    override = os.environ.get(_SANDBOX_UID_ENV_VAR, "").strip()
    if override:
        return override
    return f"{os.getuid()}:{os.getgid()}"


def container_server_params(worktree: str | Path) -> StdioServerParameters:
    """Launch params for the coder-tools server inside a throwaway container
    (docker/podman) that mounts **only** the worktree — no repo root, no
    `state/`, no keyring, no network. The single bind mount is the security
    contract; a second mount would be a security regression.

    `-i` (and no `-t`) is required: the MCP stdio transport frames JSON-RPC over
    the child's stdin/stdout pipes, so stdin must stay attached and a TTY would
    corrupt it. `-w` and the bind use the same absolute path, so the server's
    cwd is the worktree — matching the in-process/worktree tool paths that key
    off `Path.cwd()`.

    Nothing is launched here: the returned params are handed to the MCP stdio
    client. Raises `IsolationUnavailableError` if no runtime or dev image is
    available, so `container` mode fails honestly rather than silently running
    untrusted code in-process."""
    runtime = _container_runtime()
    image = os.environ.get(_DEV_IMAGE_ENV_VAR, "").strip()
    if not image:
        raise IsolationUnavailableError(
            f"container isolation requires {_DEV_IMAGE_ENV_VAR} (the dev-stage "
            "image tag holding hatch + pytest); it is unset"
        )
    wt = str(Path(worktree).resolve())
    return StdioServerParameters(
        command=runtime,
        args=[
            "run",
            "--rm",
            "-i",
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp",  # noqa: S108 — container tmpfs mount target (writable /tmp inside the sandbox), not a host temp path
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--user",
            _sandbox_user(),
            "-v",
            f"{wt}:{wt}:rw",
            "-w",
            wt,
            image,
            "python",
            "-m",
            _CODER_TOOLS_SERVER_MODULE,
        ],
        cwd=None,
    )


def sandbox_server_params(worktree: str | Path) -> StdioServerParameters:
    """Launch params for the coder-tools server inside a daemon-free `bwrap`
    sandbox — the **secondary** substrate. Read-only system dirs, the worktree
    the only writable bind, no network (`--unshare-all` includes the net
    namespace). `bwrap` also needs unprivileged user namespaces on the host
    (verify with `unshare -Ur true`).

    INERT on this branch: argv-shape tested, never launched (no runtime here).
    Raises `IsolationUnavailableError` if `bwrap` is not on PATH."""
    if shutil.which("bwrap") is None:
        raise IsolationUnavailableError(
            "sandbox isolation selected but 'bwrap' is not on PATH (it also "
            "requires unprivileged user namespaces; verify with `unshare -Ur "
            "true` on the target host)"
        )
    wt = str(Path(worktree).resolve())
    return StdioServerParameters(
        command="bwrap",
        args=[
            "--unshare-all",
            "--die-with-parent",
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--ro-bind",
            "/bin",
            "/bin",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",  # noqa: S108 — bwrap tmpfs mount target (writable /tmp inside the sandbox), not a host temp path
            "--bind",
            wt,
            wt,
            "--chdir",
            wt,
            "python",
            "-m",
            _CODER_TOOLS_SERVER_MODULE,
        ],
        cwd=None,
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


def _coder_tools_params(spec: MCPServerSpec, cwd: str | Path | None) -> StdioServerParameters:
    """The `coder_tools` server's launch params, isolation-aware. Under
    `container`/`sandbox` isolation this overrides the config entry entirely
    (mounting only the worktree, as today); otherwise it uses the config's
    local-profile `command`/`args` with `cwd` set to the per-call worktree —
    matching the pre-refactor `coder_tools_server_params(cwd)` contract."""
    mode = sandbox_runtime_mode()
    if mode == "container":
        return container_server_params(cwd if cwd is not None else Path.cwd())
    if mode == "sandbox":
        return sandbox_server_params(cwd if cwd is not None else Path.cwd())
    return StdioServerParameters(
        command=spec.command,
        args=spec.args,
        cwd=str(cwd) if cwd is not None else spec.cwd,
    )


def build_provider_for(names: list[str], *, cwd: str | Path | None = None) -> MCPToolProvider:
    """A provider scoped to exactly the named servers, materialized from
    `.mcp.json` (or its built-in default). Each consumer names only the
    servers it wants — the model's coder tool loop names `coder_tools` alone,
    so a `.mcp.json` declaring other servers (e.g. `github`) never leaks their
    tools into it. Selecting a name absent from config raises `KeyError`.

    `coder_tools` is a recognized special case (see `_coder_tools_params`);
    every other named server launches from its static config spec as-is.
    """
    config = load_mcp_config()
    params: list[StdioServerParameters] = []
    for name in names:
        if name not in config:
            raise KeyError(f"MCP server {name!r} is not declared in .mcp.json")
        spec = config[name]
        if name == CODER_TOOLS_SERVER_NAME:
            params.append(_coder_tools_params(spec, cwd))
        else:
            params.append(StdioServerParameters(command=spec.command, args=spec.args, cwd=spec.cwd))
    return MCPToolProvider(params)


def build_coder_tool_provider(cwd: str | Path | None = None) -> MCPToolProvider:
    """A provider wired to the coder-tools stdio server (the runtime tool set the
    agentic Coder uses). Under `container`/`sandbox` isolation the server is
    launched inside a sandbox mounting only the worktree; otherwise it runs as a
    local subprocess. The selected sandbox mode never degrades to in-process
    execution — a missing runtime raises `IsolationUnavailableError`."""
    return build_provider_for([CODER_TOOLS_SERVER_NAME], cwd=cwd)
