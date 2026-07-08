"""Parity tests: the LangGraph engine must satisfy the same behavioral
contract as the classic run_loop, so it reuses run_loop's own test fakes and
mirrors its scenarios against run_graph_loop."""

from pathlib import Path

import pytest

from loop_engine.core.engine import (
    MAX_ESCALATIONS_PER_STAGE,
    Loop,
    MissingArtifactError,
    Stage,
    StageGateFailedError,
)
from loop_engine.core.gates import ArtifactGate
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import IssueRef, RunStatus
from loop_engine.personas.base import BasePersona
from tests.core.test_engine import (
    AnsweringResolver,
    AppendArtifactPersona,
    QuestionAskingPersona,
    _initial_state,
    _simple_loop,
    _stage,
    _stub_llm_client,
)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _stub_issue_filer(monkeypatch):
    filed: list[list] = []

    def fake_file_issue(state, questions, snapshot_path):
        filed.append(list(questions))
        return IssueRef(number=42, url="https://github.com/example/repo/issues/42")

    monkeypatch.setattr("loop_engine.core.engine.file_question_issue", fake_file_issue)
    return filed


def test_graph_executes_stages_in_order_and_merges_state() -> None:
    final = run_graph_loop(_simple_loop(["a", "b", "c"]), _initial_state(), _stub_llm_client())

    assert final.artifacts == {"a": "done", "b": "done", "c": "done"}
    assert final.status is RunStatus.COMPLETED


def test_graph_writes_snapshot_after_each_stage_and_a_terminal_snapshot() -> None:
    run_graph_loop(_simple_loop(["a", "b"]), _initial_state("run-2"), _stub_llm_client())

    run_dir = Path("state") / "run-2"
    names = sorted(p.name for p in run_dir.glob("*.json"))
    assert names == [
        "00_AppendArtifactPersona.json",
        "01_AppendArtifactPersona.json",
        "02_completed.json",
    ]


def test_graph_missing_consumed_artifact_fails_with_snapshot() -> None:
    class NeedsInputPersona(AppendArtifactPersona):
        consumes = ("nonexistent",)

    loop = Loop(stages=[_stage(NeedsInputPersona("out"), "out")])
    with pytest.raises(MissingArtifactError, match="nonexistent"):
        run_graph_loop(loop, _initial_state("run-3"), _stub_llm_client())

    assert (Path("state") / "run-3" / "00_failed_stage.json").exists()


def test_graph_budget_exhaustion_returns_budget_exceeded_with_snapshot() -> None:
    class NeverCalledPersona(BasePersona):
        def run(self, state, llm_client, findings=None):
            raise AssertionError("this persona must never be invoked")

    loop = Loop(stages=[Stage(persona=NeverCalledPersona(), gate=ArtifactGate("x"))])
    client = _stub_llm_client(cost_used=5.0, budget_usd=5.0)

    final = run_graph_loop(loop, _initial_state("run-4"), client)

    assert final.status is RunStatus.BUDGET_EXCEEDED
    assert (Path("state") / "run-4" / "00_budget_exceeded.json").exists()


def test_graph_revise_then_accept() -> None:
    class EventuallyValidPersona(BasePersona):
        def __init__(self) -> None:
            self.attempts = 0

        def run(self, state, llm_client, findings=None):
            self.attempts += 1
            value = "" if self.attempts == 1 else "real output"
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": value}})

    loop = Loop(stages=[Stage(persona=EventuallyValidPersona(), gate=ArtifactGate("doc"))])
    final = run_graph_loop(loop, _initial_state(), _stub_llm_client())

    assert final.status is RunStatus.COMPLETED


def test_graph_no_progress_revision_escalates(_stub_issue_filer) -> None:
    class AlwaysEmptyPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state, llm_client, findings=None):
            self.calls += 1
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": ""}})

    persona = AlwaysEmptyPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"), max_revisions=3)])

    final = run_graph_loop(loop, _initial_state("run-5"), _stub_llm_client())

    assert persona.calls == 2
    assert final.status is RunStatus.AWAITING_ISSUE
    assert len(_stub_issue_filer) == 1


def test_graph_gate_failure_with_changing_findings_raises_after_cap() -> None:
    class AlternatingBadPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state, llm_client, findings=None):
            self.calls += 1
            value = "" if self.calls % 2 else "not json"
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": value}})

    loop = Loop(
        stages=[
            Stage(
                persona=AlternatingBadPersona(),
                gate=ArtifactGate("doc", parse_json="object"),
                max_revisions=1,
            )
        ]
    )
    with pytest.raises(StageGateFailedError, match="AlternatingBadPersona"):
        run_graph_loop(loop, _initial_state("run-6"), _stub_llm_client())

    assert (Path("state") / "run-6" / "00_failed_stage.json").exists()


def test_graph_escalation_resolved_by_ladder_reenters_with_findings() -> None:
    persona = QuestionAskingPersona()
    resolver = AnsweringResolver(impact="task")
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"), resolvers=[resolver])])

    final = run_graph_loop(loop, _initial_state("run-7"), _stub_llm_client())

    assert final.status is RunStatus.COMPLETED
    assert persona.calls == 2
    assert final.questions[0].resolution == "eu-west-1"


def test_graph_unresolved_questions_file_issue_and_pause(_stub_issue_filer) -> None:
    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])

    final = run_graph_loop(loop, _initial_state("run-8"), _stub_llm_client())

    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue == IssueRef(
        number=42, url="https://github.com/example/repo/issues/42"
    )
    assert [q.text for q in _stub_issue_filer[0]] == ["Which region?"]
    assert (Path("state") / "run-8" / "00_awaiting_issue.json").exists()


def test_graph_plan_impact_reenters_earlier_stage() -> None:
    executed: list[str] = []

    class RecordingPersona(AppendArtifactPersona):
        def run(self, state, llm_client, findings=None):
            executed.append(f"{self._key}{':revised' if findings else ''}")
            return super().run(state, llm_client, findings)

    asker = QuestionAskingPersona()
    resolver = AnsweringResolver(impact="plan")

    loop = Loop(
        stages=[
            _stage(RecordingPersona("plan"), "plan"),
            Stage(persona=asker, gate=ArtifactGate("doc"), resolvers=[resolver]),
        ],
        impact_reentry={"plan": 0},
    )

    final = run_graph_loop(loop, _initial_state("run-9"), _stub_llm_client())

    assert final.status is RunStatus.COMPLETED
    assert executed == ["plan", "plan:revised"]
    assert asker.calls == 2
    assert final.counters.get("replans") == 1


def test_graph_escalation_cap_files_issue_instead_of_cycling(_stub_issue_filer) -> None:
    class AlwaysAskingPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state, llm_client, findings=None):
            self.calls += 1
            doc = f"# Doc\n\n## Open Questions\n\n1. Question number {self.calls}?"
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": doc}})

    persona = AlwaysAskingPersona()
    resolver = AnsweringResolver(impact="task")
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"), resolvers=[resolver])])

    final = run_graph_loop(loop, _initial_state("run-10"), _stub_llm_client())

    assert final.status is RunStatus.AWAITING_ISSUE
    assert persona.calls == MAX_ESCALATIONS_PER_STAGE + 1
    assert len(_stub_issue_filer) == 1


def test_graph_engine_selected_by_env_flag(monkeypatch) -> None:
    from loop_engine.core.graph_engine import use_langgraph_engine

    monkeypatch.delenv("LOOP_ENGINE_ENGINE", raising=False)
    assert use_langgraph_engine() is False
    monkeypatch.setenv("LOOP_ENGINE_ENGINE", "langgraph")
    assert use_langgraph_engine() is True
