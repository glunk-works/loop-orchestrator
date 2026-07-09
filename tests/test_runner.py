from unittest.mock import MagicMock

from loop_engine.core.state import RunStatus, State
from loop_engine.runner import DEFAULT_BUDGET_USD, run_new


def _completed_state(**overrides) -> State:
    defaults = dict(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.COMPLETED,
        stage_history=[],
        artifacts={},
    )
    return State(**{**defaults, **overrides})


def test_run_new_builds_state_from_human_input_and_returns_engine_result(monkeypatch) -> None:
    captured = {}

    def fake_engine(loop, state, client, *, start_index):
        captured["loop"] = loop
        captured["state"] = state
        captured["client"] = client
        captured["start_index"] = start_index
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_engine.runner.run_loop", fake_engine)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    final_state = run_new("do the thing", budget_usd=1.23, loop_name="default")

    assert captured["state"].artifacts["human_input"] == "do the thing"
    assert captured["state"].run_id
    assert captured["start_index"] == 0
    assert final_state.run_id == captured["state"].run_id
    assert final_state.status == RunStatus.COMPLETED


def test_run_new_mints_a_fresh_run_id_each_call(monkeypatch) -> None:
    seen_run_ids = []

    def fake_engine(loop, state, client, *, start_index):
        seen_run_ids.append(state.run_id)
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_engine.runner.run_loop", fake_engine)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    run_new("first")
    run_new("second")

    assert len(seen_run_ids) == 2
    assert seen_run_ids[0] != seen_run_ids[1]


def test_run_new_dispatches_to_langgraph_engine_when_flagged(monkeypatch) -> None:
    mock_graph = MagicMock(return_value=_completed_state())
    mock_classic = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.runner.run_graph_loop", mock_graph)
    monkeypatch.setattr("loop_engine.runner.run_loop", mock_classic)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())
    monkeypatch.setenv("LOOP_ENGINE_ENGINE", "langgraph")

    run_new("hello")

    assert mock_graph.called
    assert not mock_classic.called


def test_run_new_defaults_to_classic_engine(monkeypatch) -> None:
    mock_graph = MagicMock(return_value=_completed_state())
    mock_classic = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.runner.run_graph_loop", mock_graph)
    monkeypatch.setattr("loop_engine.runner.run_loop", mock_classic)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())
    monkeypatch.delenv("LOOP_ENGINE_ENGINE", raising=False)

    run_new("hello")

    assert mock_classic.called
    assert not mock_graph.called


def test_run_new_default_budget_is_used_when_not_specified(monkeypatch) -> None:
    mock_client_cls = MagicMock()
    monkeypatch.setattr("loop_engine.runner.run_loop", MagicMock(return_value=_completed_state()))
    monkeypatch.setattr("loop_engine.runner.LLMClient", mock_client_cls)

    run_new("hello")

    mock_client_cls.assert_called_once_with(budget_usd=DEFAULT_BUDGET_USD)
