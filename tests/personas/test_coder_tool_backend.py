"""The Coder's tool backend: always MCP, with the provider opened once and
always closed.

Phase 6 deleted the in-process dispatch this used to select between. That also
retires the old "container isolation without MCP tools refuses" guard — the
refusal existed because the in-process path ran model-generated tools inside the
orchestrator process with nothing to sandbox. With that path gone the hazard is
structural rather than conditional: tool execution *only* happens in the MCP
server subprocess, so there is no unsandboxed fallback left to refuse.
"""

from loop_orchestrator.personas.coder_iac.shared import _CoderToolBackend


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


def test_backend_resolves_to_mcp_with_no_env_configuration(monkeypatch) -> None:
    # No flag is consulted any more: MCP is the tool path unconditionally.
    fake = _FakeProvider()
    monkeypatch.setattr(
        "loop_orchestrator.personas.coder_iac.shared.build_coder_tool_provider",
        lambda cwd=None: fake,
    )

    tools, execute = _CoderToolBackend().resolve()

    assert tools == fake.tools
    assert execute == fake.execute


def test_mcp_backend_opens_provider_once_and_closes(monkeypatch) -> None:
    fake = _FakeProvider()
    monkeypatch.setattr(
        "loop_orchestrator.personas.coder_iac.shared.build_coder_tool_provider",
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


def test_close_without_resolve_is_a_noop() -> None:
    _CoderToolBackend().close()  # nothing opened, nothing to close
