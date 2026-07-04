from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import State
from loop_engine.personas.coder_iac.persona import CoderIacPersona


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=1, run_id="run-1", stage_history=[], artifacts=artifacts)


def test_coder_iac_persona_raises_key_error_when_sprint_plans_missing() -> None:
    mock_llm_client = MagicMock()

    with pytest.raises(KeyError):
        CoderIacPersona().run(_state({}), mock_llm_client)


def test_coder_iac_persona_returns_non_empty_implementation_summary() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(
        text="Created src/foo.py and tests/test_foo.py."
    )

    result_state = CoderIacPersona().run(
        _state({"sprint_plans": '[{"path": "x", "content": "y"}]'}), mock_llm_client
    )

    assert result_state.artifacts["implementation_summary"]
