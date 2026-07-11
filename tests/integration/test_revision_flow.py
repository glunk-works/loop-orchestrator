"""One gate-REVISE round drives exactly two LLM requests: a full generation,
then a 3-turn targeted revision against the prior artifact."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import GateDecision, GateResult
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import RunStatus, State
from loop_engine.personas.architecture.persona import ArchitecturePersona

FIRST_ATTEMPT = "# Architecture\n\n1. Overview.\n\n## Assumptions\n\n- Single region.\n"


class ReviseOnceGate:
    """REVISEs the first artifact it sees, accepts thereafter."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, state: State, stage_name: str) -> GateResult:
        self.calls += 1
        if self.calls == 1:
            return GateResult(
                GateDecision.REVISE,
                findings=["Assumptions must name the region explicitly."],
            )
        return GateResult(GateDecision.ACCEPT)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_gate_revise_round_makes_two_calls_with_three_turn_second_request() -> None:
    llm_client = MagicMock()
    llm_client.tokens_used = 0
    llm_client.cost_used = 0.0
    llm_client.cache_creation_tokens_used = 0
    llm_client.cache_read_tokens_used = 0
    llm_client.remaining.return_value = 10.0
    llm_client.call.return_value = SimpleNamespace(text=FIRST_ATTEMPT)
    llm_client.call_messages.return_value = SimpleNamespace(
        text="## Assumptions\n\n- All compute in eu-west-1.\n"
    )

    loop = Loop(stages=[Stage(persona=ArchitecturePersona(), gate=ReviseOnceGate())])
    initial = State(
        schema_version=2,
        run_id="run-revise",
        stage_history=[],
        artifacts={"project_spec": '{"problem_statement": "x"}'},
    )

    final = run_graph_loop(loop, initial, llm_client)

    assert final.status is RunStatus.COMPLETED
    # Exactly two transport-bound requests: one full generation, one revision.
    assert llm_client.call.call_count == 1
    assert llm_client.call_messages.call_count == 1

    messages = llm_client.call_messages.call_args.args[0]
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert messages[1]["content"] == FIRST_ATTEMPT
    assert "Assumptions must name the region explicitly." in messages[2]["content"]

    # The merged artifact keeps the untouched preamble and swaps the section.
    revised = final.artifacts["architecture_definition"]
    assert revised.startswith("# Architecture\n\n1. Overview.\n")
    assert "- All compute in eu-west-1." in revised
    assert "- Single region." not in revised
