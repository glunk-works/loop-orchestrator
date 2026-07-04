from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import State
from loop_engine.personas.architecture.persona import ArchitecturePersona


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=1, run_id="run-1", stage_history=[], artifacts=artifacts)


def test_architecture_persona_raises_key_error_when_project_spec_missing() -> None:
    mock_llm_client = MagicMock()

    with pytest.raises(KeyError):
        ArchitecturePersona().run(_state({}), mock_llm_client)


def test_architecture_persona_returns_populated_architecture_definition() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text="# Architecture Definition\n...")

    result_state = ArchitecturePersona().run(
        _state({"project_spec": '{"problem_statement": "x"}'}), mock_llm_client
    )

    assert result_state.artifacts["architecture_definition"] == "# Architecture Definition\n..."
