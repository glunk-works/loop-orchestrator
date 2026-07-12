import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from loop_engine.core.engine import (
    MAX_ESCALATIONS_PER_STAGE,
    MAX_REPLANS_PER_RUN,
    InvalidStateTransitionError,
    Loop,
    MissingArtifactError,
    Stage,
    StageGateFailedError,
)
from loop_engine.core.gates import ArtifactGate
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import IssueRef, Question, RunStatus, StageRecord, State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.llm.client import ToolLoopExceededError


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _stub_issue_filer(monkeypatch):
    filed: list[list[Question]] = []

    def fake_file_issue(state, questions, snapshot_path):
        filed.append(list(questions))
        return IssueRef(number=42, url="https://github.com/example/repo/issues/42")

    monkeypatch.setattr("loop_engine.core.engine.default_issue_filer", fake_file_issue)
    return filed


def _initial_state(run_id: str = "run-1", artifacts: dict[str, str] | None = None) -> State:
    return State(
        schema_version=2,
        run_id=run_id,
        stage_history=[],
        artifacts=artifacts if artifacts is not None else {},
    )


def _stub_llm_client(cost_used: float = 0.0, budget_usd: float = 10.0) -> SimpleNamespace:
    client = SimpleNamespace(
        budget_usd=budget_usd,
        tokens_used=0,
        cost_used=cost_used,
        cache_creation_tokens_used=0,
        cache_read_tokens_used=0,
    )
    client.remaining = lambda: client.budget_usd - client.cost_used
    return client


class AppendArtifactPersona(BasePersona):
    def __init__(self, key: str) -> None:
        self._key = key

    def run(self, state: State, llm_client, findings=None) -> State:
        artifacts = {**state.artifacts, self._key: "done"}
        return state.model_copy(update={"artifacts": artifacts})


def _stage(persona: BasePersona, key: str, **kwargs) -> Stage:
    return Stage(persona=persona, gate=ArtifactGate(key), **kwargs)


def _simple_loop(keys: list[str]) -> Loop:
    return Loop(stages=[_stage(AppendArtifactPersona(k), k) for k in keys])


def test_engine_executes_stages_in_order_and_merges_state() -> None:
    final_state = run_graph_loop(
        _simple_loop(["a", "b", "c"]), _initial_state(), _stub_llm_client()
    )

    assert final_state.artifacts == {"a": "done", "b": "done", "c": "done"}
    assert final_state.status is RunStatus.COMPLETED


def test_engine_writes_snapshot_after_each_stage_and_a_terminal_snapshot() -> None:
    run_graph_loop(_simple_loop(["a", "b"]), _initial_state("run-2"), _stub_llm_client())

    run_dir = Path("state") / "run-2"
    names = sorted(p.name for p in run_dir.glob("*.json"))
    assert names == [
        "00_AppendArtifactPersona.json",
        "01_AppendArtifactPersona.json",
        "02_completed.json",
    ]
    final = State.model_validate_json((run_dir / "02_completed.json").read_text())
    assert final.status is RunStatus.COMPLETED


def test_engine_raises_invalid_state_transition_error_naming_persona() -> None:
    class CorruptingPersona(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            record = StageRecord(
                stage_name="corrupt",
                tokens_used=1,
                cost_usd=0.0,
                completed_at="2026-07-02T00:00:00Z",
            )
            state.stage_history.append(record)
            state.stage_history[0].tokens_used = -5  # bypasses construction-time validation
            return state

    loop = Loop(stages=[Stage(persona=CorruptingPersona(), gate=ArtifactGate("x"))])
    with pytest.raises(InvalidStateTransitionError, match="CorruptingPersona"):
        run_graph_loop(loop, _initial_state(), _stub_llm_client())


def test_engine_missing_consumed_artifact_fails_with_snapshot() -> None:
    class NeedsInputPersona(AppendArtifactPersona):
        consumes = ("nonexistent",)

    loop = Loop(stages=[_stage(NeedsInputPersona("out"), "out")])
    with pytest.raises(MissingArtifactError, match="nonexistent"):
        run_graph_loop(loop, _initial_state("run-3"), _stub_llm_client())

    snapshot = Path("state") / "run-3" / "00_failed_stage.json"
    assert snapshot.exists()


def test_engine_budget_exhaustion_returns_budget_exceeded_with_snapshot() -> None:
    class NeverCalledPersona(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            raise AssertionError("this persona must never be invoked")

    loop = Loop(stages=[Stage(persona=NeverCalledPersona(), gate=ArtifactGate("x"))])
    client = _stub_llm_client(cost_used=5.0, budget_usd=5.0)

    final = run_graph_loop(loop, _initial_state("run-4"), client)

    assert final.status is RunStatus.BUDGET_EXCEEDED
    assert (Path("state") / "run-4" / "00_budget_exceeded.json").exists()


def test_engine_tool_loop_exhaustion_fails_stage_cleanly_with_snapshot() -> None:
    # A persona whose inner tool loop exhausts its iteration cap must end the
    # run with a persisted FAILED_STAGE snapshot, not crash it (mirrors the
    # bounded-resource handling of BudgetExceededError).
    class StuckPersona(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            raise ToolLoopExceededError("did not converge")

    loop = Loop(stages=[Stage(persona=StuckPersona(), gate=ArtifactGate("x"))])

    final = run_graph_loop(loop, _initial_state("run-stuck"), _stub_llm_client())

    assert final.status is RunStatus.FAILED_STAGE
    assert (Path("state") / "run-stuck" / "00_failed_stage.json").exists()


def test_engine_records_real_cost_and_cache_deltas_per_stage() -> None:
    class SpendingPersona(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            llm_client.tokens_used += 100
            llm_client.cost_used += 0.25
            llm_client.cache_creation_tokens_used += 40
            llm_client.cache_read_tokens_used += 60
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": "done"}})

    loop = Loop(stages=[Stage(persona=SpendingPersona(), gate=ArtifactGate("doc"))])
    final = run_graph_loop(loop, _initial_state("run-cost"), _stub_llm_client())

    record = final.stage_history[-1]
    assert record.tokens_used == 100
    assert record.cost_usd == pytest.approx(0.25)
    assert record.cache_creation_input_tokens == 40
    assert record.cache_read_input_tokens == 60


def test_engine_revise_then_accept_passes_gate_findings_to_persona() -> None:
    received_findings: list[list[str] | None] = []

    class EventuallyValidPersona(BasePersona):
        def __init__(self) -> None:
            self.attempts = 0

        def run(self, state: State, llm_client, findings=None) -> State:
            received_findings.append(findings)
            self.attempts += 1
            value = "" if self.attempts == 1 else "real output"
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": value}})

    loop = Loop(stages=[Stage(persona=EventuallyValidPersona(), gate=ArtifactGate("doc"))])
    final = run_graph_loop(loop, _initial_state(), _stub_llm_client())

    assert final.status is RunStatus.COMPLETED
    assert received_findings[0] is None
    assert any("missing or empty" in f for f in received_findings[1])


def test_engine_no_progress_revision_escalates_instead_of_rerolling(
    _stub_issue_filer,
) -> None:
    class AlwaysEmptyPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state: State, llm_client, findings=None) -> State:
            self.calls += 1
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": ""}})

    persona = AlwaysEmptyPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"), max_revisions=3)])

    final = run_graph_loop(loop, _initial_state("run-5"), _stub_llm_client())

    # Two attempts produce identical findings; the third re-roll is not spent.
    assert persona.calls == 2
    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue is not None
    assert len(_stub_issue_filer) == 1


def test_engine_gate_failure_with_changing_findings_raises_after_cap() -> None:
    class AlternatingBadPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state: State, llm_client, findings=None) -> State:
            self.calls += 1
            # Alternate between two invalid shapes so findings keep changing.
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


def test_engine_gate_failure_with_changing_findings_escalates_when_flag_set(
    _stub_issue_filer,
) -> None:
    class AlternatingBadPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state: State, llm_client, findings=None) -> State:
            self.calls += 1
            # Alternate between two invalid shapes so findings keep changing.
            value = "" if self.calls % 2 else "not json"
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": value}})

    loop = Loop(
        stages=[
            Stage(
                persona=AlternatingBadPersona(),
                gate=ArtifactGate("doc", parse_json="object"),
                max_revisions=1,
                escalate_on_exhaustion=True,
            )
        ]
    )

    final = run_graph_loop(loop, _initial_state("run-6"), _stub_llm_client())

    # No resolver for this stage, so the escalation pauses for a human issue
    # instead of raising StageGateFailedError.
    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue is not None
    assert len(_stub_issue_filer) == 1


class QuestionAskingPersona(BasePersona):
    """Emits an artifact with an Open Questions section on the first pass."""

    def __init__(self) -> None:
        self.calls = 0

    def run(self, state: State, llm_client, findings=None) -> State:
        self.calls += 1
        if findings:
            doc = "# Doc\n\nAll ambiguities resolved."
        else:
            doc = "# Doc\n\ncontent\n\n## Open Questions\n\n1. Which region?"
        return state.model_copy(update={"artifacts": {**state.artifacts, "doc": doc}})


class AnsweringResolver(BasePersona):
    def __init__(self, impact: str = "task") -> None:
        self.impact = impact
        self.seen: list[str] = []

    def run(self, state: State, llm_client, findings=None) -> State:
        return state

    def resolve_questions(self, questions, state, llm_client):
        self.seen.extend(q.text for q in questions)
        return [
            q.model_copy(
                update={"resolution": "eu-west-1", "resolved_by": "resolver", "impact": self.impact}
            )
            for q in questions
        ]


def test_engine_escalation_resolved_by_ladder_reenters_with_findings() -> None:
    persona = QuestionAskingPersona()
    resolver = AnsweringResolver(impact="task")
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"), resolvers=[resolver])])

    final = run_graph_loop(loop, _initial_state("run-7"), _stub_llm_client())

    assert final.status is RunStatus.COMPLETED
    assert persona.calls == 2
    assert resolver.seen == ["Which region?"]
    assert final.questions[0].resolution == "eu-west-1"


def test_engine_unresolved_questions_file_issue_and_pause(_stub_issue_filer) -> None:
    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])

    final = run_graph_loop(loop, _initial_state("run-8"), _stub_llm_client())

    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue == IssueRef(
        number=42, url="https://github.com/example/repo/issues/42"
    )
    assert [q.text for q in _stub_issue_filer[0]] == ["Which region?"]
    assert (Path("state") / "run-8" / "00_awaiting_issue.json").exists()


def test_engine_pause_for_issue_persists_before_filing_survives_a_raising_filer() -> None:
    """F4: a raise inside the filer (e.g. an unresolvable escalation
    destination) must not destroy the run -- an AWAITING_ISSUE snapshot is
    persisted BEFORE the filer runs, so the run stays resumable."""
    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])

    def raising_filer(state, questions, snapshot_path):
        raise RuntimeError("gh repo view failed: not a git repository")

    with pytest.raises(RuntimeError, match="not a git repository"):
        run_graph_loop(
            loop, _initial_state("run-9b"), _stub_llm_client(), issue_filer=raising_filer
        )

    snapshot_path = Path("state") / "run-9b" / "00_awaiting_issue.json"
    assert snapshot_path.exists(), "a raising filer must not discard the run's snapshot"
    persisted = State.model_validate(json.loads(snapshot_path.read_text()))
    assert persisted.status is RunStatus.AWAITING_ISSUE
    # The filer raised before returning an IssueRef, so pending_issue is
    # still unset -- but the run itself, and its questions, survive.
    assert persisted.pending_issue is None
    assert persisted.questions[0].text == "Which region?"


class _FakeIssueProvider:
    """Stands in for an entered MCPToolProvider scoped to the `issue` server —
    no subprocess, no real `gh`."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def execute(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        return IssueRef(
            number=99, url="https://github.com/example/repo/issues/99"
        ).model_dump_json()


def test_engine_injected_mcp_issue_filer_routes_through_provider() -> None:
    from loop_engine.tools.issue_io import mcp_issue_filer

    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])
    provider = _FakeIssueProvider()

    final = run_graph_loop(
        loop, _initial_state("run-8b"), _stub_llm_client(), issue_filer=mcp_issue_filer(provider)
    )

    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue == IssueRef(
        number=99, url="https://github.com/example/repo/issues/99"
    )
    assert provider.calls[0][0] == "create_issue"


def test_engine_uninjected_default_filer_names_an_explicit_destination_repo(monkeypatch) -> None:
    """The path `runner.run_new` actually takes: NO `issue_filer` injected, so
    `_pause_for_issue` falls through to `default_issue_filer`.

    Every other test in this module stubs that default out via the autouse
    fixture, which is precisely why the original R8 fix shipped covering only
    `cli.py` — the fresh-run paths kept filing issues against whatever repo the
    worktree CWD resolved to, and CI stayed green. This test opts out of the
    stub and pins the real default: it must dispatch `create_issue` with an
    explicit, non-null `repo`.
    """
    from loop_engine.tools.issue_io import default_issue_filer as real_default_issue_filer

    provider = _FakeIssueProvider()
    # Restore the real default over the autouse stub (a bare `monkeypatch.undo()`
    # would also undo `_isolated_cwd`, spraying snapshots into the repo).
    monkeypatch.setattr("loop_engine.core.engine.default_issue_filer", real_default_issue_filer)
    monkeypatch.setattr(
        "loop_engine.tools.mcp.build_issue_provider",
        lambda: _ContextManagerProvider(provider),
    )
    monkeypatch.setattr(
        "loop_engine.tools.repo_io.resolve_repo_slug", lambda cwd: "acme/managed-repo"
    )

    loop = Loop(stages=[Stage(persona=QuestionAskingPersona(), gate=ArtifactGate("doc"))])
    final = run_graph_loop(loop, _initial_state("run-8c"), _stub_llm_client())

    assert final.status is RunStatus.AWAITING_ISSUE
    verb, args = provider.calls[0]
    assert verb == "create_issue"
    assert args["repo"] == "acme/managed-repo", (
        "the un-injected default must name its destination explicitly, not let "
        "`gh` infer it from the worktree CWD (finding R8)"
    )


class _ContextManagerProvider:
    """Wraps a fake provider so it can stand in for `build_issue_provider()`,
    which the default filer enters as a context manager."""

    def __init__(self, inner: _FakeIssueProvider) -> None:
        self._inner = inner

    def __enter__(self) -> _FakeIssueProvider:
        return self._inner

    def __exit__(self, *exc_info: object) -> None:
        return None


def test_engine_injected_mcp_issue_filer_routes_through_provider_at_escalation_cap() -> None:
    """R4: the escalation-cap pause site (site 2 of 3) also honors an
    injected filer, not just the default-path stub."""
    from loop_engine.tools.issue_io import mcp_issue_filer

    class AlwaysAskingPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state: State, llm_client, findings=None) -> State:
            self.calls += 1
            doc = f"# Doc\n\n## Open Questions\n\n1. Question number {self.calls}?"
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": doc}})

    persona = AlwaysAskingPersona()
    resolver = AnsweringResolver(impact="task")
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"), resolvers=[resolver])])
    provider = _FakeIssueProvider()

    final = run_graph_loop(
        loop, _initial_state("run-10b"), _stub_llm_client(), issue_filer=mcp_issue_filer(provider)
    )

    assert final.status is RunStatus.AWAITING_ISSUE
    assert persona.calls == MAX_ESCALATIONS_PER_STAGE + 1
    assert final.pending_issue == IssueRef(
        number=99, url="https://github.com/example/repo/issues/99"
    )
    assert provider.calls[0][0] == "create_issue"


def test_engine_injected_mcp_issue_filer_routes_through_provider_at_replan_cap() -> None:
    """R4: the replan-cap pause site (site 3 of 3) also honors an injected
    filer. Pre-seeding `counters["replans"]` at the cap makes the very first
    escalation on this stage hit the replan-cap branch directly, since a
    single stage re-escalating trips its own per-stage escalation cap first
    (both caps are 2) before a multi-round scenario could ever reach the
    replan-cap branch."""
    from loop_engine.tools.issue_io import mcp_issue_filer

    persona = QuestionAskingPersona()
    resolver = AnsweringResolver(impact="plan")
    loop = Loop(
        stages=[
            _stage(AppendArtifactPersona("plan"), "plan"),
            Stage(persona=persona, gate=ArtifactGate("doc"), resolvers=[resolver]),
        ],
        impact_reentry={"plan": 0},
    )
    initial = _initial_state("run-10c")
    initial = initial.model_copy(
        update={"counters": {**initial.counters, "replans": MAX_REPLANS_PER_RUN}}
    )
    provider = _FakeIssueProvider()

    final = run_graph_loop(loop, initial, _stub_llm_client(), issue_filer=mcp_issue_filer(provider))

    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue == IssueRef(
        number=99, url="https://github.com/example/repo/issues/99"
    )
    assert provider.calls[0][0] == "create_issue"


def test_engine_plan_impact_reenters_earlier_stage() -> None:
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
    # plan runs, asker escalates, plan re-runs with findings, asker re-runs.
    assert executed == ["plan", "plan:revised"]
    assert asker.calls == 2
    assert final.counters.get("replans") == 1


def test_engine_escalation_cap_files_issue_instead_of_cycling(_stub_issue_filer) -> None:
    class AlwaysAskingPersona(BasePersona):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, state: State, llm_client, findings=None) -> State:
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


def test_engine_terminal_snapshot_exists_for_every_status(tmp_path) -> None:
    # COMPLETED covered above; verify the awaiting-issue terminal snapshot
    # round-trips with pending_issue and questions intact.
    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])
    run_graph_loop(loop, _initial_state("run-11"), _stub_llm_client())

    snapshot_path = Path("state") / "run-11" / "00_awaiting_issue.json"
    snapshot = State.model_validate(json.loads(snapshot_path.read_text()))
    assert snapshot.status is RunStatus.AWAITING_ISSUE
    assert snapshot.pending_issue is not None
    assert snapshot.questions and snapshot.questions[0].resolution is None
