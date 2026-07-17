import json
import logging
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from loop_engine.core.engine import (
    MAX_ESCALATIONS_PER_STAGE,
    MAX_REPLANS_PER_RUN,
    PAUSED_STAGE_COUNTER,
    InvalidStateTransitionError,
    Loop,
    MissingArtifactError,
    Stage,
    StageGateFailedError,
    _merge_questions,
    _run_resolver_ladder,
    apply_resolved_answers,
    reentry_index,
)
from loop_engine.core.gates import ArtifactGate, GateDecision, GateResult
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import IssueRef, Question, RunStatus, SlackRef, StageRecord, State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.llm.client import (
    BudgetExceededError,
    ToolLoopExceededError,
    TruncatedResponseError,
)
from tests.core.conftest import absolutize_mutmut_source_paths


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    absolutize_mutmut_source_paths(monkeypatch)
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

    persona = AlternatingBadPersona()
    loop = Loop(
        stages=[
            Stage(
                persona=persona,
                gate=ArtifactGate("doc", parse_json="object"),
                max_revisions=1,
            )
        ]
    )
    with pytest.raises(
        StageGateFailedError, match="AlternatingBadPersona failed its gate after 2 attempts"
    ):
        run_graph_loop(loop, _initial_state("run-6"), _stub_llm_client())

    # Real off-by-one gap (Sprint 38 T3, BL-23): pin the EXACT attempt count
    # (max_revisions + 1 == 2), not just the exception type/persona name, so an
    # extra/missing revision iteration is caught.
    assert persona.calls == 2
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
    # Real boundary gap (Sprint 38 T3, BL-23): `reentry < stage_index` -> `<=`
    # would misclassify this same-stage (task-impact) reentry as a replan.
    assert "replans" not in final.counters


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
    # Real gap (Sprint 38 T3, BL-23): the pause-bookkeeping counter must
    # actually be recorded (not skipped, not written under a typo'd key) so a
    # later resume can find the stage it paused at.
    assert final.counters.get(PAUSED_STAGE_COUNTER) == 0


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
    `_pause_for_escalation` falls through to `default_issue_filer`.

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


# --- Sprint 41 T2 (BL-2 pass 3): transport-agnostic EscalationFiler seam ---


def test_engine_slack_ref_pause_finalizes_awaiting_slack_and_sets_pending_slack() -> None:
    """FD4/finding #12: `_pause_for_escalation` dispatches on the returned
    ref's TYPE, not on any transport flag -- an injected filer returning a
    `SlackRef` finalizes AWAITING_SLACK and stores `pending_slack`, never
    `pending_issue`, even though no real Slack filer exists yet (T3)."""

    def slack_filer(state: State, questions: list[Question], snapshot_hint: str) -> SlackRef:
        return SlackRef(channel_id="C123", message_ts="1700000000.000100")

    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])

    final = run_graph_loop(
        loop, _initial_state("run-slack"), _stub_llm_client(), issue_filer=slack_filer
    )

    assert final.status is RunStatus.AWAITING_SLACK
    assert final.pending_slack == SlackRef(channel_id="C123", message_ts="1700000000.000100")
    assert final.pending_issue is None
    assert (Path("state") / "run-slack" / "00_awaiting_slack.json").exists()


def test_engine_issue_ref_pause_still_sets_pending_issue_not_pending_slack() -> None:
    """The inverse of the above: an `IssueRef`-returning filer (the default
    shape) must never touch `pending_slack`, confirming the ref-type dispatch
    is genuinely two-way, not just "anything not IssueRef -> Slack"."""

    def issue_filer(state: State, questions: list[Question], snapshot_hint: str) -> IssueRef:
        return IssueRef(number=7, url="https://github.com/example/repo/issues/7")

    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])

    final = run_graph_loop(
        loop, _initial_state("run-issue-ref"), _stub_llm_client(), issue_filer=issue_filer
    )

    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue == IssueRef(number=7, url="https://github.com/example/repo/issues/7")
    assert final.pending_slack is None


# --- Sprint 38 T3 (BL-23): landing audit_report.md's `fix` verdicts ---


def test_engine_record_stage_completed_at_has_utc_offset() -> None:
    # Real gap: `datetime.now(UTC)` weakened to `datetime.now(None)` (naive
    # local time) is unobservable unless something checks the timestamp
    # actually carries a UTC offset.
    loop = Loop(stages=[_stage(AppendArtifactPersona("doc"), "doc")])
    final = run_graph_loop(loop, _initial_state("run-utc"), _stub_llm_client())

    completed_at = datetime.fromisoformat(final.stage_history[0].completed_at)
    assert completed_at.tzinfo is not None


def test_engine_logs_stage_completion_with_distinct_nonzero_values(caplog) -> None:
    # Real gaps: `_record_stage`'s log call can drop/null any of `stage_name`,
    # `cost_usd`, `cache_creation_input_tokens`, `cache_read_input_tokens`
    # (silently defaulting via `log_stage_completion`'s own defaults) without
    # any existing test noticing, because none pinned the exact values logged.
    class SpendingPersona(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            llm_client.tokens_used += 111
            llm_client.cost_used += 0.37
            llm_client.cache_creation_tokens_used += 41
            llm_client.cache_read_tokens_used += 59
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": "done"}})

    loop = Loop(stages=[Stage(persona=SpendingPersona(), gate=ArtifactGate("doc"))])

    with caplog.at_level(logging.INFO, logger="loop_engine.cost"):
        run_graph_loop(loop, _initial_state("run-log"), _stub_llm_client())

    records = [r for r in caplog.records if r.name == "loop_engine.cost"]
    assert len(records) == 1
    payload = json.loads(records[0].message)
    assert payload["stage_name"] == "SpendingPersona"
    assert payload["tokens_used"] == 111
    assert payload["cost_usd"] == pytest.approx(0.37)
    assert payload["cache_creation_input_tokens"] == 41
    assert payload["cache_read_input_tokens"] == 59


def test_merge_questions_replaces_already_recorded_question_by_id() -> None:
    # Real gap: `by_id.get(q.id, q)` defaulted to None would drop a
    # question's prior (unresolved) record instead of replacing it with its
    # newly-resolved version -- exercised only when a question with the same
    # id is ALREADY in state.questions (the human-answer-resume shape).
    stale = Question(id="q1", origin_stage="S", text="Which region?")
    resolved = stale.model_copy(
        update={"resolution": "eu-west-1", "resolved_by": "pm", "impact": "task"}
    )
    state = _initial_state().model_copy(update={"questions": [stale]})

    merged = _merge_questions(state, [resolved])

    assert merged.questions == [resolved]


def test_run_resolver_ladder_stops_once_all_resolved_by_an_earlier_resolver() -> None:
    # Real gap: `break` weakened to a bare `return` (returning None instead
    # of `current`) is only observable with 2+ resolvers where an earlier one
    # fully resolves -- every other test uses a single-resolver ladder.
    q = Question(id="q1", origin_stage="S", text="Which region?")

    class FullyResolvingResolver(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            return state

        def resolve_questions(self, questions, state, llm_client):
            return [
                qq.model_copy(
                    update={"resolution": "eu-west-1", "resolved_by": "architect", "impact": "task"}
                )
                for qq in questions
            ]

    class ExplodingResolver(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            return state

        def resolve_questions(self, questions, state, llm_client):
            raise AssertionError("must never be reached once the ladder is fully resolved")

    stage = Stage(
        persona=AppendArtifactPersona("doc"),
        gate=ArtifactGate("doc"),
        resolvers=[FullyResolvingResolver(), ExplodingResolver()],
    )

    result = _run_resolver_ladder(stage, [q], _initial_state(), _stub_llm_client())

    assert result[0].resolution == "eu-west-1"


def test_engine_threads_state_and_llm_client_through_resolver_ladder() -> None:
    # Real gap: both the `_run_resolver_ladder` call site (in execute_stage)
    # and its own call to `resolver.resolve_questions` can pass None instead
    # of the real `state`/`llm_client` -- every AnsweringResolver test double
    # ignores both arguments, masking either mutation.
    seen: list[tuple[object, object]] = []

    class RecordingResolver(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            return state

        def resolve_questions(self, questions, state, llm_client):
            seen.append((state, llm_client))
            return [
                q.model_copy(
                    update={"resolution": "eu-west-1", "resolved_by": "architect", "impact": "task"}
                )
                for q in questions
            ]

    persona = QuestionAskingPersona()
    resolver = RecordingResolver()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"), resolvers=[resolver])])
    client = _stub_llm_client()

    final = run_graph_loop(loop, _initial_state("run-thread"), client)

    assert final.status is RunStatus.COMPLETED
    assert len(seen) == 1
    seen_state, seen_client = seen[0]
    assert isinstance(seen_state, State)
    assert seen_client is client


def test_run_resolver_ladder_partial_answer_falls_through_to_next_resolver() -> None:
    # Real gap: `answered_by_id.get(q.id, q)` defaulted to None would drop a
    # question the FIRST resolver didn't answer instead of carrying it
    # forward unchanged -- only observable when a resolver answers a subset
    # of what it's given (every AnsweringResolver test double answers 100%).
    q1 = Question(id="q1", origin_stage="S", text="Which region?")
    q2 = Question(id="q2", origin_stage="S", text="Which tier?")

    class PartialResolver(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            return state

        def resolve_questions(self, questions, state, llm_client):
            return [
                q.model_copy(
                    update={"resolution": "eu-west-1", "resolved_by": "architect", "impact": "task"}
                )
                for q in questions
                if q.id == "q1"
            ]

    class SecondResolver(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            return state

        def resolve_questions(self, questions, state, llm_client):
            return [
                q.model_copy(update={"resolution": "gold", "resolved_by": "pm", "impact": "task"})
                for q in questions
            ]

    stage = Stage(
        persona=AppendArtifactPersona("doc"),
        gate=ArtifactGate("doc"),
        resolvers=[PartialResolver(), SecondResolver()],
    )

    result = _run_resolver_ladder(stage, [q1, q2], _initial_state(), _stub_llm_client())

    by_id = {q.id: q for q in result}
    assert by_id["q1"].resolution == "eu-west-1"
    assert by_id["q2"].resolution == "gold"


def test_engine_no_progress_escalation_joins_multiple_findings_with_semicolon(
    _stub_issue_filer,
) -> None:
    # Real gap: the join separator "; " -> "XX; XX" is invisible whenever the
    # findings list being joined has exactly one item (every existing
    # no-progress test uses a single-finding gate).
    def two_finding_gate(state: State, stage_name: str) -> GateResult:
        return GateResult(GateDecision.REVISE, findings=["finding A", "finding B"])

    loop = Loop(
        stages=[Stage(persona=AppendArtifactPersona("doc"), gate=two_finding_gate, max_revisions=3)]
    )

    final = run_graph_loop(loop, _initial_state("run-sep"), _stub_llm_client())

    assert final.status is RunStatus.AWAITING_ISSUE
    question_text = _stub_issue_filer[0][0].text
    assert "finding A; finding B" in question_text


def test_engine_gate_failed_error_joins_multiple_findings_with_semicolon() -> None:
    # Same join-separator gap as above, on the OTHER message-building call
    # site: the hard StageGateFailedError raised when revisions are exhausted
    # with findings still changing (so no-progress escalation never fires).
    calls = {"n": 0}

    def two_finding_gate(state: State, stage_name: str) -> GateResult:
        calls["n"] += 1
        return GateResult(
            GateDecision.REVISE, findings=[f"finding A{calls['n']}", f"finding B{calls['n']}"]
        )

    loop = Loop(
        stages=[Stage(persona=AppendArtifactPersona("doc"), gate=two_finding_gate, max_revisions=1)]
    )

    with pytest.raises(StageGateFailedError) as exc_info:
        run_graph_loop(loop, _initial_state("run-hardfail"), _stub_llm_client())

    assert f"finding A{calls['n']}; finding B{calls['n']}" in str(exc_info.value)


def test_reentry_index_architecture_impact_reenters_configured_stage() -> None:
    # Real gap: no test ever resolves a question with impact="architecture"
    # (every resolver-ladder test uses "task" or "plan"), so the literal
    # "architecture" comparison in `reentry_index` is unconstrained.
    loop = Loop(stages=[], impact_reentry={"architecture": 0, "plan": 1})
    resolved = [
        Question(
            id="q1",
            origin_stage="S",
            text="t?",
            resolution="ans",
            resolved_by="architect",
            impact="architecture",
        )
    ]

    assert reentry_index(loop, 5, resolved) == 0


def test_reentry_index_requires_both_impact_present_and_configured() -> None:
    # Real gap: `and` -> `or` would reenter even when the resolved impact is
    # "task" (not "architecture"), just because the loop happens to configure
    # an "architecture" re-entry point for some OTHER question.
    loop = Loop(stages=[], impact_reentry={"architecture": 0})
    resolved = [
        Question(
            id="q1",
            origin_stage="S",
            text="t?",
            resolution="ans",
            resolved_by="pm",
            impact="task",
        )
    ]

    assert reentry_index(loop, 5, resolved) == 5


def _paused_questions_state() -> State:
    return State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={},
        questions=[
            Question(id="q1", origin_stage="ArchitectureGenerator", text="Which region?"),
            Question(id="q2", origin_stage="CoderIacPersona", text="OIDC or API keys?"),
        ],
    )


def test_apply_resolved_answers_marks_filed_questions_resolved_in_order() -> None:
    state = _paused_questions_state()

    updated, resolved_ids = apply_resolved_answers(state, {1: "eu-west-1"}, "human:17")

    assert updated.questions[0].resolution == "eu-west-1"
    assert updated.questions[0].resolved_by == "human:17"
    assert updated.questions[1].resolution is None
    assert resolved_ids == {"q1"}


def test_apply_resolved_answers_ignores_out_of_range_numbers() -> None:
    state = _paused_questions_state()

    updated, resolved_ids = apply_resolved_answers(state, {5: "nonsense"}, "human:17")

    assert all(q.resolution is None for q in updated.questions)
    assert resolved_ids == set()


def test_apply_resolved_answers_resolved_by_is_provenance_only() -> None:
    # Finding #4: the Slack transport's resolved_by shape differs from the
    # issue transport's, and the returned id set must not depend on it.
    state = _paused_questions_state()

    updated, resolved_ids = apply_resolved_answers(
        state, {1: "eu-west-1", 2: "OIDC"}, "human:slack:1700000000.000100"
    )

    assert {q.resolved_by for q in updated.questions} == {"human:slack:1700000000.000100"}
    assert resolved_ids == {"q1", "q2"}


def test_engine_pause_for_issue_passes_correct_snapshot_hint() -> None:
    # Real gap: `snapshot_hint` can be forced to None or dropped at the
    # `issue_filer` call site -- the autouse `_stub_issue_filer` fixture's
    # fake filer ignores its `snapshot_path` argument entirely, so no test
    # observes this value without its own recording filer.
    seen_hints: list[str] = []

    def recording_filer(state: State, questions: list[Question], snapshot_hint: str) -> IssueRef:
        seen_hints.append(snapshot_hint)
        return IssueRef(number=42, url="https://github.com/example/repo/issues/42")

    persona = QuestionAskingPersona()
    loop = Loop(stages=[Stage(persona=persona, gate=ArtifactGate("doc"))])

    final = run_graph_loop(
        loop, _initial_state("run-hint"), _stub_llm_client(), issue_filer=recording_filer
    )

    assert final.status is RunStatus.AWAITING_ISSUE
    assert seen_hints == ["state/run-hint/00_awaiting_issue.json"]


def test_engine_resume_with_carried_findings_clears_counter_and_respects_carried_until() -> None:
    """Real gap (untested resume path): `initial_findings` is non-empty in
    exactly one production caller (cli.py's resume-from-issue), and every
    other test calls the REAL run_graph_loop with an empty/fresh state, so
    `_prime_resume`'s `if carried_findings:` branch -- the only place
    PAUSED_STAGE_COUNTER/`loop` are read -- never executes. Seed a State
    carrying the pause counter (as `_pause_for_escalation` would have recorded
    it) and pass non-empty `initial_findings`, mirroring `cli.py`'s
    `resume --from-issue` shape."""
    received_findings: list[list[str] | None] = []

    class RecordingPersona(AppendArtifactPersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            received_findings.append(findings)
            return super().run(state, llm_client, findings)

    loop = Loop(stages=[_stage(RecordingPersona("a"), "a"), _stage(RecordingPersona("b"), "b")])
    paused_state = _initial_state("run-resume").model_copy(
        update={"counters": {PAUSED_STAGE_COUNTER: 0}}
    )

    final = run_graph_loop(
        loop,
        paused_state,
        _stub_llm_client(),
        start_index=0,
        initial_findings=["Resolution: answer"],
    )

    assert final.status is RunStatus.COMPLETED
    # Stage 0 (stage_index <= carried_until==0) receives the carried finding...
    assert received_findings[0] == ["Resolution: answer"]
    # ...but stage 1 (stage_index > carried_until==0) does not carry it forward.
    assert received_findings[1] is None
    # The pause bookkeeping counter is cleared on resume, not left stale.
    assert PAUSED_STAGE_COUNTER not in final.counters


def test_engine_resume_without_pause_counter_falls_back_to_last_stage_index() -> None:
    """Real gap: `_prime_resume`'s fallback default --
    `state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)` -- is
    only reached when `initial_findings` is non-empty but the state carries
    NO pause counter at all. The sibling resume test above always seeds a
    counter, so it never reaches this `.get(...)` default. Use a 3-stage loop
    so the correct default (last stage index, 2) is distinguishable from an
    off-by-one default (1) at the LAST stage specifically."""
    received_findings: list[list[str] | None] = []

    class RecordingPersona(AppendArtifactPersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            received_findings.append(findings)
            return super().run(state, llm_client, findings)

    loop = Loop(
        stages=[
            _stage(RecordingPersona("a"), "a"),
            _stage(RecordingPersona("b"), "b"),
            _stage(RecordingPersona("c"), "c"),
        ]
    )

    final = run_graph_loop(
        loop,
        _initial_state("run-resume-no-counter"),
        _stub_llm_client(),
        start_index=0,
        initial_findings=["Resolution: answer"],
    )

    assert final.status is RunStatus.COMPLETED
    # Every stage index is <= the correct default (2, the last stage) --
    # including the LAST stage, which an off-by-one-low default would miss.
    assert received_findings == [
        ["Resolution: answer"],
        ["Resolution: answer"],
        ["Resolution: answer"],
    ]


def test_engine_reentry_boundary_stage_index_equals_carried_until_still_gets_findings() -> None:
    # Real off-by-one: `stage_index > carried_until` -> `>=`. The existing
    # plan-impact-reentry test can't observe this because its gate treats an
    # already-resolved question's text as answered regardless of `findings`
    # (masking the difference); record `findings` directly on the asking
    # persona instead of relying on its gate's behavior.
    received_by_asker: list[list[str] | None] = []

    class RecordingAsker(QuestionAskingPersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            received_by_asker.append(findings)
            return super().run(state, llm_client, findings)

    asker = RecordingAsker()
    resolver = AnsweringResolver(impact="plan")
    loop = Loop(
        stages=[
            _stage(AppendArtifactPersona("plan"), "plan"),
            Stage(persona=asker, gate=ArtifactGate("doc"), resolvers=[resolver]),
        ],
        impact_reentry={"plan": 0},
    )

    final = run_graph_loop(loop, _initial_state("run-boundary"), _stub_llm_client())

    assert final.status is RunStatus.COMPLETED
    assert received_by_asker[0] is None
    # Second call is the re-entered asker at stage_index == carried_until:
    # findings must still be delivered, not reset to empty.
    assert received_by_asker[1]


def test_engine_present_consumed_artifact_does_not_raise() -> None:
    # Killed-elsewhere gap: `has_artifact(state, None)` (always False) is only
    # caught by an integration test outside tests/core/ -- the local
    # `consumes`-check test here only exercises the "missing" branch, never
    # the "present" branch.
    class NeedsInputPersona(AppendArtifactPersona):
        consumes = ("dep",)

    loop = Loop(stages=[_stage(NeedsInputPersona("out"), "out")])
    final = run_graph_loop(
        loop, _initial_state("run-present", artifacts={"dep": "value"}), _stub_llm_client()
    )

    assert final.status is RunStatus.COMPLETED


def test_engine_budget_check_boundary_partial_remaining_still_runs_stage() -> None:
    # Real boundary gap: `llm_client.remaining() <= 0` -> `<= 1`. The only
    # existing budget-exhaustion test sets remaining() to exactly 0.0, where
    # both conditions agree; pin a remaining() strictly between 0 and 1.
    loop = Loop(stages=[_stage(AppendArtifactPersona("doc"), "doc")])
    client = _stub_llm_client(cost_used=9.5, budget_usd=10.0)  # remaining() == 0.5

    final = run_graph_loop(loop, _initial_state("run-partial-budget"), client)

    assert final.status is RunStatus.COMPLETED


def test_engine_budget_exceeded_mid_revision_loop_ends_stage_cleanly() -> None:
    # tests/core/ has no coverage of the `except BudgetExceededError:` block
    # INSIDE the revision loop (a persona raising it directly) -- the only
    # existing budget-exhaustion test here triggers the earlier PRE-persona
    # `remaining() <= 0` check instead, which never calls persona.run() at all.
    class BudgetBlowingPersona(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            raise BudgetExceededError("out of budget mid-stage")

    loop = Loop(stages=[Stage(persona=BudgetBlowingPersona(), gate=ArtifactGate("doc"))])

    final = run_graph_loop(loop, _initial_state("run-mid-budget"), _stub_llm_client())

    assert final.status is RunStatus.BUDGET_EXCEEDED
    assert (Path("state") / "run-mid-budget" / "00_budget_exceeded.json").exists()


def test_engine_truncated_response_error_fails_stage_with_invalid_state_transition() -> None:
    # No test anywhere in the suite raises TruncatedResponseError through a
    # real persona path -- unlike the sibling BudgetExceededError block,
    # there is no tests/integration/ analog that hits this one either.
    class TruncatingPersona(BasePersona):
        def run(self, state: State, llm_client, findings=None) -> State:
            raise TruncatedResponseError("response cut off mid-JSON")

    loop = Loop(stages=[Stage(persona=TruncatingPersona(), gate=ArtifactGate("doc"))])

    with pytest.raises(InvalidStateTransitionError, match="TruncatingPersona"):
        run_graph_loop(loop, _initial_state("run-truncated"), _stub_llm_client())

    assert (Path("state") / "run-truncated" / "00_failed_stage.json").exists()


def test_engine_two_stage_spending_records_per_stage_deltas_not_cumulative() -> None:
    # Real gaps: the tokens_used/cost_usd/cache_*_tokens delta subtraction
    # (`X - before`) flipped to addition is invisible from a single stage off
    # a zero baseline (`X - 0 == X + 0`) -- only a second stage, where
    # `before` is nonzero, distinguishes delta from cumulative total.
    class SpendingPersona(BasePersona):
        def __init__(
            self, key: str, tokens: int, cost: float, cache_creation: int, cache_read: int
        ) -> None:
            self._key = key
            self._tokens = tokens
            self._cost = cost
            self._cache_creation = cache_creation
            self._cache_read = cache_read

        def run(self, state: State, llm_client, findings=None) -> State:
            llm_client.tokens_used += self._tokens
            llm_client.cost_used += self._cost
            llm_client.cache_creation_tokens_used += self._cache_creation
            llm_client.cache_read_tokens_used += self._cache_read
            return state.model_copy(update={"artifacts": {**state.artifacts, self._key: "done"}})

    loop = Loop(
        stages=[
            Stage(persona=SpendingPersona("a", 100, 0.10, 10, 20), gate=ArtifactGate("a")),
            Stage(persona=SpendingPersona("b", 50, 0.05, 5, 15), gate=ArtifactGate("b")),
        ]
    )

    final = run_graph_loop(loop, _initial_state("run-two-stage-cost"), _stub_llm_client())

    first, second = final.stage_history
    assert first.tokens_used == 100
    assert first.cost_usd == pytest.approx(0.10)
    assert first.cache_creation_input_tokens == 10
    assert first.cache_read_input_tokens == 20

    assert second.tokens_used == 50
    assert second.cost_usd == pytest.approx(0.05)
    assert second.cache_creation_input_tokens == 5
    assert second.cache_read_input_tokens == 15
