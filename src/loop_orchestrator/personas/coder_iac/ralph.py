"""The Ralph-loop Coder: one task per invocation, from a fresh context.

The Ralph Coder does exactly ONE task per invocation and returns, letting the
engine's existing revise loop (`execute_stage`) re-enter it until the
coverage-aware gate is green. (The classic per-sprint Coder it replaced iterated
every sprint in a single `run()`; Phase 6 deleted it.) Progress is the
`.agent/STATE.md` task checklist; the manifest is the immutable backlog; the
worktree filesystem is the memory.

When every task is checked off but the suite is red (a cross-task regression),
the gate emits a `RALPH_REGRESSION_PREFIX` finding and this persona runs a
**repair increment** instead of no-opping — so "loop until green" holds for
regressions too, not just for unbuilt tasks.

Since Phase 6 this is the only Coder — `LOOP_ENGINE_CODER` and the classic
per-sprint Coder are deleted. It was always a behavior change rather than a
refactor, so it was never parity-tested against the classic Coder; its sunset
justification was a real multi-sprint host run reaching COMPLETED under the full
production config (verification V2, sprint 27).
"""

import json
import logging
import re

from loop_orchestrator.core.coder_gate import EDIT_FAILURES_HEADER, RALPH_REGRESSION_PREFIX
from loop_orchestrator.core.gates import RESOLUTION_FINDING_PREFIX, extract_open_questions
from loop_orchestrator.core.state import Question, State
from loop_orchestrator.personas.agile_sprint_breakdown.manifest import TaskEntry
from loop_orchestrator.personas.base import BasePersona
from loop_orchestrator.personas.coder_iac.shared import (
    MAX_TOKENS,
    PROMPT_TEMPLATE,
    _CoderToolBackend,
    apply_file_blocks,
    sprint_report_path,
)
from loop_orchestrator.tools.agent_state import (
    MemoryEntry,
    ScratchpadState,
    append_memory,
    read_scratchpad,
    write_scratchpad,
)
from loop_orchestrator.tools.llm.client import ToolLoopExceededError
from loop_orchestrator.tools.llm.pricing import DEFAULT_MODEL
from loop_orchestrator.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)

_REGRESSION_SECTION_HEADER = "### Regression fix"


def select_next_task(manifest: list[TaskEntry], done: list[str]) -> TaskEntry | None:
    """The first manifest task not yet done whose deps are all done.

    Manifest order is plan order, so this respects sprint/task sequencing; the
    dependency check additionally blocks a task until its prerequisites land.
    """
    done_set = set(done)
    for task in manifest:
        if task.id in done_set:
            continue
        if all(dep in done_set for dep in task.deps):
            return task
    return None


def _split_findings(findings: list[str] | None) -> tuple[list[str], str | None]:
    """Partition carried findings into resolution answers and the latest gate
    status line. Resolution answers (carried across the whole Coder stage) are
    all kept in the prompt; only the most recent status/regression line is —
    stale intermediate status lines would just be noise. Fixes the old
    `findings[-1]`-only behavior that dropped resolutions after one iteration.
    """
    if not findings:
        return [], None
    resolutions = [f for f in findings if f.startswith(RESOLUTION_FINDING_PREFIX)]
    status = [f for f in findings if not f.startswith(RESOLUTION_FINDING_PREFIX)]
    return resolutions, (status[-1] if status else None)


def _compose_findings(resolutions: list[str], latest_status: str | None) -> str | None:
    parts = [*resolutions]
    if latest_status:
        parts.append(latest_status)
    return "\n\n".join(parts) if parts else None


def _upsert_task_section(existing: str, header: str, body: str) -> str:
    """Replace the block starting with `header` (up to the next section header or
    end) with a fresh one, or append it if absent — so re-running an escalated
    task, or a repeated repair increment, never duplicates its report section.

    The terminator matches only the section headers *this* module writes
    (`### Task ` / `### Regression fix`), NOT any `### ` — a model report body
    routinely contains its own `### ` subheadings, and a bare-`### ` terminator
    would stop mid-body and orphan the tail (leaking stale content, including a
    resolved `## Edit Application Failures`, across re-runs).
    """
    section = f"{header}\n\n{body}"
    if not existing:
        return section
    pattern = re.compile(
        rf"^{re.escape(header)}.*?(?=\n### Task |\n{re.escape(_REGRESSION_SECTION_HEADER)}|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    if pattern.search(existing):
        return pattern.sub(lambda _match: section, existing, count=1)
    return f"{existing}\n\n{section}"


def _build_task_prompt(
    task: TaskEntry, sprint_content: str, composed_findings: str | None, completed: list[str]
) -> str:
    parts = [
        "You are working this project ONE task at a time. Implement exactly the "
        "single task below — not the whole sprint, not later tasks.",
        f"\nTask id: {task.id}\nSprint: {task.sprint_path}\nTitle: {task.title}",
        f"\nDescription:\n{task.description}",
        f"\nTarget Files: {', '.join(task.target_files) or 'unspecified'}",
        f"\nAcceptance Criteria:\n{task.acceptance_criteria}",
        f"\nParent sprint context (for reference only):\n{sprint_content}",
    ]
    if completed:
        parts.append("\nAlready-completed tasks: " + ", ".join(completed))
    if composed_findings:
        parts.append(f"\nLatest gate status / resolutions to address:\n{composed_findings}")
    parts.append(
        "\nImplement only this task and write its acceptance-criteria test. Run the "
        "tests before finishing. If a test you authored yourself (in this or an earlier "
        "increment) fails or conflicts with correct code, fix or remove that test — this is "
        "in scope for every increment regardless of which task first added it. Reserve "
        "`## Open Questions` for genuine ambiguities in the task specification itself; never "
        "raise one about a test of your own authorship."
    )
    return "\n".join(parts)


def _build_repair_prompt(composed_findings: str | None, completed: list[str]) -> str:
    parts = [
        "Every task in the manifest is complete, but the full test suite is RED: a "
        "recent change regressed a previously-passing test. Diagnose the failure and "
        "fix it. Do NOT add new features, new tasks, or new scope — repair only the "
        "regression so the whole suite is green again.",
    ]
    if completed:
        parts.append("\nCompleted tasks: " + ", ".join(completed))
    if composed_findings:
        parts.append(f"\nGate status / failing tests to address:\n{composed_findings}")
    parts.append(
        "\nUse your tools to locate the failing test(s) and the change that broke them. "
        "Run the tests before finishing. If the regression traces to a test you authored "
        "yourself, fix or remove that test — this is in scope for every increment. Reserve "
        "`## Open Questions` for genuine ambiguities in the fix itself; never raise one about "
        "a test of your own authorship."
    )
    return "\n".join(parts)


def _run_increment(llm_client, architecture: str, prompt: str) -> str:
    """One fresh-context tool loop; returns the stripped report text.

    A tool loop that exhausts its iteration cap is degraded to an empty report
    (not a crash): the increment is treated exactly like a no-output turn, so
    the caller leaves the task unchecked, the loop re-selects it with a fresh
    context, and the engine's identical-findings guard escalates if it stays
    stuck. Iteration exhaustion is a bounded-resource failure like budget
    exhaustion — it must fail the increment honestly, never abort the run.
    """
    system_blocks = [
        PROMPT_TEMPLATE,
        f"Architecture Definition Document:\n\n{architecture}",
    ]
    tool_backend = _CoderToolBackend()
    try:
        tools, execute = tool_backend.resolve()
        response = llm_client.run_tool_loop(
            [{"role": "user", "content": prompt}],
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS,
            tools=tools,
            execute=execute,
            system_blocks=system_blocks,
        )
    except ToolLoopExceededError:
        logger.warning("Ralph increment tool loop did not converge; treating as no output")
        return ""
    finally:
        tool_backend.close()
    return response.text.strip()


def _finalize_report(report: str) -> tuple[str, list[str]]:
    """Append the edit-failure section if any model edit blocks did not apply.

    Returns the (possibly failure-annotated) report text and the raw failure
    list, so callers can tell whether this increment's edit actually applied
    — a task must not be marked done on the strength of report text alone.
    """
    failures = apply_file_blocks(report)
    if failures:
        failure_lines = "\n".join(f"- {failure}" for failure in failures)
        report += f"\n\n{EDIT_FAILURES_HEADER}\n\n{failure_lines}"
    return report, failures


def _load_reports(state: State) -> dict[str, str]:
    try:
        return json.loads(state.artifacts.get("implementation_reports", "{}"))
    except json.JSONDecodeError:
        return {}


def _write_report(reports: dict[str, str], sprint_path: str, header: str, report: str) -> None:
    reports[sprint_path] = _upsert_task_section(reports.get(sprint_path, ""), header, report)
    report_path = sprint_report_path(sprint_path)
    if report_path is not None:
        try:
            write_artifact(reports[sprint_path], report_path)
        except ValueError:
            logger.warning("skipping report with invalid path %r", report_path)


def _new_questions(state: State, report: str, origin_detail: str | None) -> list[Question]:
    existing_texts = {q.text for q in state.questions}
    update = {"origin_detail": origin_detail} if origin_detail is not None else {}
    return [
        q.model_copy(update=update)
        for q in extract_open_questions(report, "RalphCoderPersona")
        if q.text not in existing_texts
    ]


class RalphCoderPersona(BasePersona):
    consumes = ("architecture_definition", "sprint_plans", "task_manifest")
    produces = ("implementation_reports",)

    def run(self, state: State, llm_client, findings: list[str] | None = None) -> State:
        architecture = state.artifacts["architecture_definition"]
        sprint_blocks = json.loads(state.artifacts["sprint_plans"])
        manifest = [
            TaskEntry.model_validate(item) for item in json.loads(state.artifacts["task_manifest"])
        ]

        scratch = read_scratchpad()
        resolutions, latest_status = _split_findings(findings)
        composed = _compose_findings(resolutions, latest_status)

        task = select_next_task(manifest, scratch.completed_tasks)
        if task is None:
            # No selectable task. If the gate reported a regression (all tasks
            # done but the suite is red), repair it; otherwise this is a true
            # no-op — the gate decides ACCEPT (all done, green) vs escalate
            # (still-blocked work).
            if latest_status is not None and latest_status.startswith(RALPH_REGRESSION_PREFIX):
                return self._repair(
                    state, llm_client, architecture, sprint_blocks, composed, scratch
                )
            return state

        return self._task_increment(
            state, llm_client, architecture, sprint_blocks, task, composed, scratch
        )

    def _task_increment(
        self, state, llm_client, architecture, sprint_blocks, task, composed, scratch
    ) -> State:
        content_by_path = {block["path"]: block["content"] for block in sprint_blocks}
        prompt = _build_task_prompt(
            task, content_by_path.get(task.sprint_path, ""), composed, scratch.completed_tasks
        )
        report = _run_increment(llm_client, architecture, prompt)
        if not report:
            # No output — do not mark done; the loop re-selects this task and the
            # engine's identical-findings guard escalates if it stays stuck.
            logger.warning("empty Ralph response for task %s", task.id)
            return state

        report, edit_failures = _finalize_report(report)
        reports = _load_reports(state)
        _write_report(reports, task.sprint_path, f"### Task {task.id}: {task.title}", report)

        new_questions = _new_questions(state, report, origin_detail=task.id)
        questions = [*state.questions, *new_questions]

        # One `.agent/` memory append per increment; mark the task done only if
        # it neither escalated nor failed to apply its edit (either case leaves
        # the task uncompleted so the loop re-selects it: on resolution for an
        # escalation, on retry for a mechanical edit-application failure — the
        # two are kept distinct per FD3, not conflated into one blocked state).
        if new_questions:
            outcome = (
                f"Blocked task {task.id} ({task.title}): "
                f"escalated {len(new_questions)} question(s)."
            )
            blocked = list(dict.fromkeys([*scratch.blocked_items, task.id]))
            write_scratchpad(
                scratch.model_copy(update={"active_task": task.id, "blocked_items": blocked})
            )
        elif edit_failures:
            outcome = f"Task {task.id} ({task.title}): edit application failed; will retry."
            write_scratchpad(scratch.model_copy(update={"active_task": task.id}))
        else:
            outcome = f"Completed task {task.id}: {task.title}."
            write_scratchpad(
                scratch.model_copy(
                    update={
                        "active_task": None,
                        "completed_tasks": [*scratch.completed_tasks, task.id],
                    }
                )
            )
        append_memory(MemoryEntry(title=f"Ralph increment — {task.id}", body=outcome))

        artifacts = {**state.artifacts, "implementation_reports": json.dumps(reports)}
        return state.model_copy(update={"artifacts": artifacts, "questions": questions})

    def _repair(
        self,
        state: State,
        llm_client,
        architecture: str,
        sprint_blocks: list[dict],
        composed: str | None,
        scratch: ScratchpadState,
    ) -> State:
        """Fix a cross-task regression: the manifest is complete but the suite is
        red. Runs one fresh-context increment, marks no task, and upserts a single
        `### Regression fix` report section so repeated repairs stay bounded."""
        prompt = _build_repair_prompt(composed, scratch.completed_tasks)
        report = _run_increment(llm_client, architecture, prompt)
        if not report:
            logger.warning("empty Ralph repair response")
            return state

        report, _edit_failures = _finalize_report(report)
        reports = _load_reports(state)
        # Attribute the fix to the last sprint in plan order (where a regression
        # is most likely to have landed); it never marks a task done.
        target_path = sprint_blocks[-1]["path"] if sprint_blocks else None
        if target_path is not None:
            _write_report(reports, target_path, _REGRESSION_SECTION_HEADER, report)

        new_questions = _new_questions(state, report, origin_detail=None)
        questions = [*state.questions, *new_questions]
        write_scratchpad(scratch.model_copy(update={"active_task": None}))
        # An escalating repair raised questions instead of fixing the suite — the
        # ledger must not claim a fix that did not happen (the gate re-runs and
        # the questions escalate via the content gate).
        if new_questions:
            outcome = (
                f"Regression repair escalated {len(new_questions)} question(s); not yet fixed."
            )
        else:
            outcome = "Repaired a cross-task test regression (no new task)."
        append_memory(MemoryEntry(title="Ralph regression fix", body=outcome))

        artifacts = {**state.artifacts, "implementation_reports": json.dumps(reports)}
        return state.model_copy(update={"artifacts": artifacts, "questions": questions})
