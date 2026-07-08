"""The Coder's tool-backend selector: in-process by default, MCP behind the
flag, with the provider opened once and always closed."""

import pytest

from loop_engine.personas.coder_iac.persona import (
    CODER_TOOLS,
    _CoderToolBackend,
    _execute_tool,
)
from loop_engine.tools.isolation import IsolationUnavailableError


class _FakeProvider:
    def __init__(self) -> None:
        self.entered = 0
        self.exited = 0
        self.tools = [{"name": "read_file", "description": "", "input_schema": {}}]

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, *exc):
        self.exited += 1

    def execute(self, name, arguments):
        return "mcp-result"


def test_default_backend_is_in_process(monkeypatch) -> None:
    monkeypatch.delenv("LOOP_ENGINE_TOOLS", raising=False)
    backend = _CoderToolBackend()

    tools, execute = backend.resolve()
    assert tools is CODER_TOOLS
    assert execute is _execute_tool

    backend.close()  # no-op when nothing was opened


def test_container_isolation_without_mcp_tools_refuses(monkeypatch) -> None:
    """container/sandbox isolation only sandboxes the MCP server; on the
    in-process path there is nothing to sandbox, so resolve() must refuse rather
    than run untrusted tools in-process."""
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")
    monkeypatch.delenv("LOOP_ENGINE_TOOLS", raising=False)
    backend = _CoderToolBackend()
    with pytest.raises(IsolationUnavailableError, match="LOOP_ENGINE_TOOLS=mcp"):
        backend.resolve()


def test_mcp_backend_opens_provider_once_and_closes(monkeypatch) -> None:
    fake = _FakeProvider()
    monkeypatch.setenv("LOOP_ENGINE_TOOLS", "mcp")
    monkeypatch.setattr(
        "loop_engine.personas.coder_iac.persona.build_coder_tool_provider",
        lambda cwd=None: fake,
    )

    backend = _CoderToolBackend()
    tools_a, execute_a = backend.resolve()
    tools_b, execute_b = backend.resolve()

    assert tools_a == fake.tools
    assert execute_a == fake.execute
    assert fake.entered == 1  # opened once, reused across sprints
    assert (tools_b, execute_b) == (tools_a, execute_a)

    backend.close()
    assert fake.exited == 1
    # Idempotent close.
    backend.close()
    assert fake.exited == 1
