"""The Ralph-loop Coder: one task per invocation, from a fresh context.

Where the classic `CoderIacPersona` iterates every sprint in a single `run()`,
the Ralph Coder does exactly ONE task per invocation and returns, letting the
engine's existing revise loop (`execute_stage`) re-enter it until the
coverage-aware gate is green. Progress is the `.agent/STATE.md` task checklist;
the manifest is the immutable backlog; the worktree filesystem is the memory.

Selected by `LOOP_ENGINE_CODER=ralph`; the classic per-sprint Coder is the
default. This is a behavior change, not a refactor — it is not parity-tested
against the classic Coder.
"""

import json
import logging

from loop_engine.core.coder_gate import EDIT_FAILURES_HEADER
from loop_engine.core.gates import extract_open_questions
from loop_engine.core.state import State
from loop_engine.personas.agile_sprint_breakdown.manifest import TaskEntry
from loop_engine.personas.base import BasePersona
from loop_engine.personas.coder_iac.shared import (
    DEFAULT_MODEL,
    MAX_TOKENS,
    PROMPT_TEMPLATE,
    _CoderToolBackend,
    apply_file_blocks,
    sprint_report_path,
)
from loop_engine.tools.agent_state import (
    MemoryEntry,
    append_memory,
    read_scratchpad,
    write_scratchpad,
)
from loop_engine.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)


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


def _build_task_prompt(
    task: TaskEntry, sprint_content: str, latest_finding: str | None, completed: list[str]
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
    if latest_finding:
        parts.append(f"\nLatest gate status / resolutions to address:\n{latest_finding}")
    parts.append(
        "\nImplement only this task and write its acceptance-criteria test. Run the "
        "tests before finishing. If a genuine ambiguity blocks the task, add a "
        "`## Open Questions` section instead of guessing."
    )
    return "\n".join(parts)


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
        task = select_next_task(manifest, scratch.completed_tasks)
        if task is None:
            # Nothing with satisfied deps remains — a no-op; the gate decides
            # ACCEPT (all tasks checked) vs REVISE (still-blocked work).
            return state

        content_by_path = {block["path"]: block["content"] for block in sprint_blocks}
        latest_finding = findings[-1] if findings else None
        prompt = _build_task_prompt(
            task, content_by_path.get(task.sprint_path, ""), latest_finding, scratch.completed_tasks
        )
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
        finally:
            tool_backend.close()

        report = response.text.strip()
        if not report:
            # No output — do not mark done; the loop re-selects this task and the
            # engine's identical-findings guard escalates if it stays stuck.
            logger.warning("empty Ralph response for task %s", task.id)
            return state

        failures = apply_file_blocks(report)
        if failures:
            failure_lines = "\n".join(f"- {failure}" for failure in failures)
            report += f"\n\n{EDIT_FAILURES_HEADER}\n\n{failure_lines}"

        try:
            reports: dict[str, str] = json.loads(
                state.artifacts.get("implementation_reports", "{}")
            )
        except json.JSONDecodeError:
            reports = {}
        section = f"### Task {task.id}: {task.title}\n\n{report}"
        reports[task.sprint_path] = (
            f"{reports[task.sprint_path]}\n\n{section}" if task.sprint_path in reports else section
        )
        report_path = sprint_report_path(task.sprint_path)
        if report_path is not None:
            try:
                write_artifact(reports[task.sprint_path], report_path)
            except ValueError:
                logger.warning("skipping report with invalid path %r", report_path)

        questions = list(state.questions)
        existing_texts = {q.text for q in questions}
        new_questions = [
            q.model_copy(update={"origin_detail": task.id})
            for q in extract_open_questions(report, "RalphCoderPersona")
            if q.text not in existing_texts
        ]
        questions.extend(new_questions)

        # One `.agent/` memory append per non-noop increment; mark the task done
        # only if it did not escalate (an escalating task stays uncompleted).
        if new_questions:
            outcome = (
                f"Blocked task {task.id} ({task.title}): "
                f"escalated {len(new_questions)} question(s)."
            )
            blocked = list(dict.fromkeys([*scratch.blocked_items, task.id]))
            write_scratchpad(
                scratch.model_copy(update={"active_task": task.id, "blocked_items": blocked})
            )
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
