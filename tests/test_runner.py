from pathlib import Path
from unittest.mock import MagicMock

import pytest

from loop_orchestrator import runner as runner_module
from loop_orchestrator.core.engine import Loop, Stage
from loop_orchestrator.core.state import Question, RunStatus, State
from loop_orchestrator.loops.default.loop import DEFAULT_LOOP
from loop_orchestrator.runner import (
    DEFAULT_BUDGET_USD,
    LoopHasNoFoldAnswersPersonaError,
    resume_run,
    run_in_tree,
    run_new,
)


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

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

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

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

    run_new("first")
    run_new("second")

    assert len(seen_run_ids) == 2
    assert seen_run_ids[0] != seen_run_ids[1]


def test_run_new_always_drives_the_langgraph_engine(monkeypatch) -> None:
    # Phase 6: the engine is unconditional — there is no flag and no alternative
    # driver to fall back to (the classic `run_loop` is deleted).
    mock_graph = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", mock_graph)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

    run_new("hello")

    assert mock_graph.called


def test_run_new_default_budget_is_used_when_not_specified(monkeypatch) -> None:
    mock_client_cls = MagicMock()
    monkeypatch.setattr(
        "loop_orchestrator.runner.run_graph_loop", MagicMock(return_value=_completed_state())
    )
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", mock_client_cls)

    run_new("hello")

    mock_client_cls.assert_called_once_with(budget_usd=DEFAULT_BUDGET_USD)


def test_run_in_tree_runs_engine_inside_tree_path_and_restores_cwd(monkeypatch, tmp_path) -> None:
    origin = Path.cwd()
    captured = {}

    def fake_engine(loop, state, client, *, start_index):
        captured["cwd"] = Path.cwd()
        captured["state"] = state
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

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

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", raising_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

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

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

    run_in_tree("first", tmp_path)
    run_in_tree("second", tmp_path)

    assert len(seen_run_ids) == 2
    assert seen_run_ids[0] != seen_run_ids[1]


def test_run_in_tree_never_opens_worktree_run_even_with_isolation_flagged(
    monkeypatch, tmp_path
) -> None:
    """With LOOP_ORCHESTRATOR_ISOLATION=worktree set, run_in_tree must still run in
    tree_path (not .worktrees/<run_id>) — it never calls worktree_run."""
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "worktree")
    captured = {}

    def fake_engine(loop, state, client, *, start_index):
        captured["cwd"] = Path.cwd()
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

    run_in_tree("hello", tmp_path)

    assert captured["cwd"] == tmp_path.resolve()
    assert ".worktrees" not in str(captured["cwd"])


def _paused_state() -> State:
    return State(
        schema_version=2,
        run_id="run-1",
        counters={"paused_stage_index": 1},
        questions=[
            Question(id="q1", origin_stage="ArchitectureGenerator", text="Which region?"),
        ],
        stage_history=[],
        artifacts={"project_spec": "{}"},
    )


def test_resume_run_applies_answers_folds_and_reenters(monkeypatch) -> None:
    fold_result_holder = {}

    def fake_fold(self, state, llm_client):
        fold_result_holder["questions"] = state.questions
        return state

    monkeypatch.setattr(type(DEFAULT_LOOP.stages[0].persona), "fold_answers", fake_fold)

    def fake_engine(loop, state, client, *, start_index, initial_findings=None, resuming=False):
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

    final_state = resume_run(_paused_state(), {1: "eu-west-1"}, resolved_by="human:17")

    assert final_state.status == RunStatus.COMPLETED
    assert fold_result_holder["questions"][0].resolution == "eu-west-1"
    assert fold_result_holder["questions"][0].resolved_by == "human:17"


def test_resume_run_reentry_and_findings_key_on_explicit_resolved_ids(monkeypatch) -> None:
    # Finding #4: the resolved set drives reentry_index/findings, and must
    # come from the explicit applied-answer ids -- not a resolved_by match.
    monkeypatch.setattr(
        type(DEFAULT_LOOP.stages[0].persona), "fold_answers", lambda self, state, llm: state
    )
    captured = {}

    def fake_engine(loop, state, client, *, start_index, initial_findings=None, resuming=False):
        captured["start_index"] = start_index
        captured["initial_findings"] = initial_findings
        captured["resuming"] = resuming
        return _completed_state(run_id=state.run_id)

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", fake_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

    resume_run(_paused_state(), {1: "eu-west-1"}, resolved_by="human:slack:1700000000.000100")

    # No impact classified (fold_answers is a no-op stub here) -> default
    # reentry at the paused stage.
    assert captured["start_index"] == 1
    assert any("eu-west-1" in f for f in captured["initial_findings"])
    assert captured["resuming"] is True


def test_resume_run_raises_value_error_without_a_fold_answers_persona(monkeypatch) -> None:
    class _NoFoldPersona:
        def run(self, state, llm_client, findings=None):
            return state

    bare_loop = Loop(stages=[Stage(persona=_NoFoldPersona(), gate=MagicMock())])
    monkeypatch.setitem(runner_module.NAMED_LOOPS, "bare", bare_loop)

    with pytest.raises(LoopHasNoFoldAnswersPersonaError, match="no answer-folding persona"):
        resume_run(_paused_state(), {1: "eu-west-1"}, resolved_by="human:17", loop_name="bare")


def test_resume_run_does_not_swallow_a_value_error_raised_deep_in_the_loop(monkeypatch) -> None:
    # A ValueError from inside fold_answers/run_graph_loop (e.g. bad env-var
    # config) is a different failure than "no fold_answers persona" and must
    # propagate uncaught, not get relabeled as LoopHasNoFoldAnswersPersonaError.
    monkeypatch.setattr(
        type(DEFAULT_LOOP.stages[0].persona), "fold_answers", lambda self, state, llm: state
    )

    def raising_engine(loop, state, client, *, start_index, initial_findings=None, resuming=False):
        raise ValueError("LOOP_ORCHESTRATOR_RALPH_MAX_ITERS is not an integer")

    monkeypatch.setattr("loop_orchestrator.runner.run_graph_loop", raising_engine)
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", MagicMock())

    with pytest.raises(ValueError, match="RALPH_MAX_ITERS") as exc_info:
        resume_run(_paused_state(), {1: "eu-west-1"}, resolved_by="human:17")

    assert not isinstance(exc_info.value, LoopHasNoFoldAnswersPersonaError)


def test_resume_run_default_budget_is_used_when_not_specified(monkeypatch) -> None:
    monkeypatch.setattr(
        type(DEFAULT_LOOP.stages[0].persona), "fold_answers", lambda self, state, llm: state
    )
    monkeypatch.setattr(
        "loop_orchestrator.runner.run_graph_loop",
        lambda loop, state, client, **kwargs: _completed_state(run_id=state.run_id),
    )
    mock_client_cls = MagicMock()
    monkeypatch.setattr("loop_orchestrator.runner.LLMClient", mock_client_cls)

    resume_run(_paused_state(), {1: "eu-west-1"}, resolved_by="human:17")

    mock_client_cls.assert_called_once_with(budget_usd=DEFAULT_BUDGET_USD)
