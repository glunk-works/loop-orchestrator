from pathlib import Path
from unittest.mock import MagicMock

from loop_engine.core.state import RunStatus, State
from loop_engine.runner import DEFAULT_BUDGET_USD, run_in_tree, run_new


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

    monkeypatch.setattr("loop_engine.runner.run_graph_loop", fake_engine)
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

    monkeypatch.setattr("loop_engine.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    run_new("first")
    run_new("second")

    assert len(seen_run_ids) == 2
    assert seen_run_ids[0] != seen_run_ids[1]


def test_run_new_always_drives_the_langgraph_engine(monkeypatch) -> None:
    # Phase 6: the engine is unconditional — there is no flag and no alternative
    # driver to fall back to (the classic `run_loop` is deleted).
    mock_graph = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.runner.run_graph_loop", mock_graph)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    run_new("hello")

    assert mock_graph.called


def test_run_new_default_budget_is_used_when_not_specified(monkeypatch) -> None:
    mock_client_cls = MagicMock()
    monkeypatch.setattr(
        "loop_engine.runner.run_graph_loop", MagicMock(return_value=_completed_state())
    )
    monkeypatch.setattr("loop_engine.runner.LLMClient", mock_client_cls)

    run_new("hello")

    mock_client_cls.assert_called_once_with(budget_usd=DEFAULT_BUDGET_USD)


def test_run_in_tree_runs_engine_inside_tree_path_and_restores_cwd(monkeypatch, tmp_path) -> None:
    origin = Path.cwd()
    captured = {}

    def fake_engine(loop, state, client, *, start_index):
        captured["cwd"] = Path.cwd()
        captured["state"] = state
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_engine.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    final_state = run_in_tree("do the thing", tmp_path, budget_usd=1.23, loop_name="default")

    assert captured["cwd"] == tmp_path.resolve()
    assert Path.cwd() == origin
    assert captured["state"].artifacts["human_input"] == "do the thing"
    assert captured["state"].run_id
    assert final_state.run_id == captured["state"].run_id
    assert final_state.status == RunStatus.COMPLETED


def test_run_in_tree_restores_cwd_even_if_engine_raises(monkeypatch, tmp_path) -> None:
    origin = Path.cwd()

    def raising_engine(loop, state, client, *, start_index):
        raise RuntimeError("boom")

    monkeypatch.setattr("loop_engine.runner.run_graph_loop", raising_engine)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    try:
        run_in_tree("hello", tmp_path)
    except RuntimeError:
        pass

    assert Path.cwd() == origin


def test_run_in_tree_mints_a_fresh_run_id(monkeypatch, tmp_path) -> None:
    seen_run_ids = []

    def fake_engine(loop, state, client, *, start_index):
        seen_run_ids.append(state.run_id)
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_engine.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    run_in_tree("first", tmp_path)
    run_in_tree("second", tmp_path)

    assert len(seen_run_ids) == 2
    assert seen_run_ids[0] != seen_run_ids[1]


def test_run_in_tree_never_opens_worktree_run_even_with_isolation_flagged(
    monkeypatch, tmp_path
) -> None:
    """With LOOP_ENGINE_ISOLATION=worktree set, run_in_tree must still run in
    tree_path (not .worktrees/<run_id>) — it never calls worktree_run."""
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "worktree")
    captured = {}

    def fake_engine(loop, state, client, *, start_index):
        captured["cwd"] = Path.cwd()
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_engine.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    run_in_tree("hello", tmp_path)

    assert captured["cwd"] == tmp_path.resolve()
    assert ".worktrees" not in str(captured["cwd"])
