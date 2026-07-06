"""The loop engine: a bounded propose → gate → (accept | revise | escalate)
state machine per stage, with an escalation ladder for questions and
blast-radius routing for rework.

Every exit path — success or any failure — persists a snapshot whose stage
name says what happened, so no paid work is ever lost to a traceback.
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import UTC, datetime

from pydantic import ValidationError

from loop_engine.core.gates import ArtifactGate, GateDecision, GateResult, new_question
from loop_engine.core.state import Question, RunStatus, StageRecord, State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.issue_io import file_question_issue
from loop_engine.tools.llm.client import BudgetExceededError, LLMClient, TruncatedResponseError
from loop_engine.tools.logging_config import log_stage_completion
from loop_engine.tools.state_io.writer import write_state_snapshot

# Hard caps on feedback edges so no cycle can run unboundedly: hitting a cap
# escalates to the human issue rather than looping again.
MAX_ESCALATIONS_PER_STAGE = 2
MAX_REPLANS_PER_RUN = 2

# Engine bookkeeping kept in State.counters so a paused run can be resumed at
# the right stage without guessing from stage_history (which may contain
# replays after blast-radius re-entry).
PAUSED_STAGE_COUNTER = "paused_stage_index"


class InvalidStateTransitionError(Exception):
    pass


class MissingArtifactError(Exception):
    pass


class StageGateFailedError(Exception):
    pass


@dataclass
class Stage:
    persona: BasePersona
    gate: ArtifactGate
    # Escalation ladder for this stage's questions, nearest resolver first
    # (e.g. Coder: [architect, pm]). Questions no resolver answers go to the
    # human as a GitHub issue.
    resolvers: list[BasePersona] = dataclass_field(default_factory=list)
    max_revisions: int = 2


@dataclass
class Loop:
    stages: list[Stage]
    # Blast-radius routing: which stage index to re-enter at when a resolved
    # question's impact is "plan" or "architecture". "task" always re-enters
    # the stage that asked.
    impact_reentry: dict[str, int] = dataclass_field(default_factory=dict)

    def stage_names(self) -> list[str]:
        return [type(stage.persona).__name__ for stage in self.stages]


def _revalidate(state: State, stage_name: str) -> State:
    try:
        return State.model_validate(state.model_dump())
    except ValidationError as exc:
        raise InvalidStateTransitionError(f"{stage_name} returned an invalid State: {exc}") from exc


def _record_stage(state: State, stage_name: str, tokens_used: int) -> State:
    # cost_usd is a placeholder until a per-model $/token rate table is
    # added; no such rate exists anywhere in this codebase or the specs.
    record = StageRecord(
        stage_name=stage_name,
        tokens_used=tokens_used,
        cost_usd=0.0,
        completed_at=datetime.now(UTC).isoformat(),
    )
    log_stage_completion(
        stage_name=record.stage_name,
        tokens_used=record.tokens_used,
        cost_usd=record.cost_usd,
    )
    return state.model_copy(update={"stage_history": [*state.stage_history, record]})


def _finalize(state: State, stage_index: int, status: RunStatus) -> State:
    """Persist a terminal snapshot for ANY exit path and stamp the status."""
    final = state.model_copy(update={"status": status})
    write_state_snapshot(
        final,
        run_id=final.run_id,
        stage_index=stage_index,
        stage_name=status.value,
    )
    return final


def _merge_questions(state: State, updated: list[Question]) -> State:
    by_id = {q.id: q for q in updated}
    merged = [by_id.get(q.id, q) for q in state.questions]
    known_ids = {q.id for q in state.questions}
    merged.extend(q for q in updated if q.id not in known_ids)
    return state.model_copy(update={"questions": merged})


def _run_resolver_ladder(
    stage: Stage, questions: list[Question], state: State, llm_client: LLMClient
) -> list[Question]:
    """Walk unresolved questions up this stage's resolver chain."""
    current = questions
    for resolver in stage.resolvers:
        unresolved = [q for q in current if q.resolution is None]
        if not unresolved:
            break
        answered = resolver.resolve_questions(unresolved, state, llm_client)
        answered_by_id = {q.id: q for q in answered}
        current = [answered_by_id.get(q.id, q) for q in current]
    return current


def _resolution_findings(questions: list[Question]) -> list[str]:
    return [
        f"Escalated question: {q.text}\n  Resolution: {q.resolution}"
        for q in questions
        if q.resolution is not None
    ]


def reentry_index(loop: Loop, stage_index: int, resolved: list[Question]) -> int:
    """Worst impact among resolutions decides how far back the run re-enters."""
    impacts = {q.impact for q in resolved if q.resolution is not None}
    for impact in ("architecture", "plan"):
        if impact in impacts and impact in loop.impact_reentry:
            return min(loop.impact_reentry[impact], stage_index)
    return stage_index


def unresolved_questions(state: State) -> list[Question]:
    """The stable filing/answering order for a paused run's open questions.

    Both the engine (when filing an issue) and the CLI (when mapping numbered
    issue answers back to questions on resume) must use this exact ordering.
    """
    return [q for q in state.questions if q.resolution is None]


def _pause_for_issue(state: State, stage_index: int, questions: list[Question]) -> State:
    state = state.model_copy(
        update={"counters": {**state.counters, PAUSED_STAGE_COUNTER: stage_index}}
    )
    snapshot_hint = f"state/{state.run_id}/{stage_index:02d}_{RunStatus.AWAITING_ISSUE.value}.json"
    issue = file_question_issue(state, questions, snapshot_hint)
    state = state.model_copy(update={"pending_issue": issue})
    return _finalize(state, stage_index, RunStatus.AWAITING_ISSUE)


def run_loop(
    loop: Loop,
    initial_state: State,
    llm_client: LLMClient,
    start_index: int = 0,
    initial_findings: list[str] | None = None,
) -> State:
    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
    stage_index = start_index

    # Resolutions produced by an escalation batch, delivered as findings to
    # every stage from the re-entry point through the stage that escalated
    # (rework stages need the answers as much as the asker does). On resume
    # after an issue round-trip the CLI passes the human answers in via
    # initial_findings, applied through the stage the run paused on.
    carried_findings: list[str] = list(initial_findings or [])
    carried_until = -1
    if carried_findings:
        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
    if PAUSED_STAGE_COUNTER in state.counters:
        state = state.model_copy(
            update={
                "counters": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
            }
        )

    while stage_index < len(loop.stages):
        stage = loop.stages[stage_index]
        stage_name = type(stage.persona).__name__

        if stage_index > carried_until:
            carried_findings = []

        missing = [k for k in stage.persona.consumes if not state.artifacts.get(k, "").strip()]
        if missing:
            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
            raise MissingArtifactError(
                f"Stage {stage_index} ({stage_name}) requires artifact(s) {missing} "
                "which no prior stage produced."
            )

        if llm_client.remaining() <= 0:
            return _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED)

        stage_findings = list(carried_findings)
        gate_result = GateResult(GateDecision.REVISE)
        previous_gate_findings: list[str] | None = None
        tokens_before = llm_client.tokens_used

        for _attempt in range(stage.max_revisions + 1):
            try:
                state = stage.persona.run(state, llm_client, findings=stage_findings or None)
            except BudgetExceededError:
                return _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED)
            except TruncatedResponseError as exc:
                # Truncation is an output-sizing failure a blind retry won't
                # fix; fail the stage honestly with the snapshot persisted.
                state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
                raise InvalidStateTransitionError(
                    f"{stage_name} produced a truncated response: {exc}"
                ) from exc

            state = _revalidate(state, stage_name)
            gate_result = stage.gate(state, stage_name)

            if gate_result.decision is not GateDecision.REVISE:
                break
            if gate_result.findings == previous_gate_findings:
                # The gate said the same thing twice: another attempt would
                # be an identical re-roll. Escalate instead of spending it.
                gate_result = GateResult(
                    GateDecision.ESCALATE,
                    questions=[
                        new_question(
                            stage_name,
                            f"{stage_name} could not satisfy its output gate after "
                            f"repeated attempts: {'; '.join(gate_result.findings)}",
                        )
                    ],
                )
                break
            previous_gate_findings = gate_result.findings
            stage_findings = [*stage_findings, *gate_result.findings]

        if gate_result.decision is GateDecision.REVISE:
            # Revision budget exhausted with findings still changing.
            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
            raise StageGateFailedError(
                f"{stage_name} failed its gate after {stage.max_revisions + 1} attempts: "
                f"{'; '.join(gate_result.findings)}"
            )

        if gate_result.decision is GateDecision.ESCALATE:
            counter_key = f"escalations:{stage_name}"
            escalations = state.counters.get(counter_key, 0)
            state = state.model_copy(
                update={"counters": {**state.counters, counter_key: escalations + 1}}
            )

            if escalations >= MAX_ESCALATIONS_PER_STAGE:
                state = _merge_questions(state, gate_result.questions)
                return _pause_for_issue(state, stage_index, unresolved_questions(state))

            resolved = _run_resolver_ladder(stage, gate_result.questions, state, llm_client)
            state = _merge_questions(state, resolved)

            if unresolved_questions(state):
                return _pause_for_issue(state, stage_index, unresolved_questions(state))

            # Everything was resolved within the ladder: deliver resolutions
            # as findings and route rework by blast radius.
            carried_findings = _resolution_findings(resolved)
            carried_until = stage_index
            reentry = reentry_index(loop, stage_index, resolved)
            if reentry < stage_index:
                replans = state.counters.get("replans", 0)
                if replans >= MAX_REPLANS_PER_RUN:
                    return _pause_for_issue(state, stage_index, resolved)
                state = state.model_copy(
                    update={"counters": {**state.counters, "replans": replans + 1}}
                )
            stage_index = reentry
            continue

        # ACCEPT
        state = _record_stage(state, stage_name, llm_client.tokens_used - tokens_before)
        write_state_snapshot(
            state,
            run_id=state.run_id,
            stage_index=stage_index,
            stage_name=stage_name,
        )
        stage_index += 1

    return _finalize(state, len(loop.stages), RunStatus.COMPLETED)
