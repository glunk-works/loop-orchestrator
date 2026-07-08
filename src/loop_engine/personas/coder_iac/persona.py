import json
import logging

from loop_engine.core.coder_gate import EDIT_FAILURES_HEADER
from loop_engine.core.gates import extract_open_questions
from loop_engine.core.state import State
from loop_engine.personas import sections
from loop_engine.personas.base import BasePersona
from loop_engine.personas.coder_iac.shared import (
    DEFAULT_MODEL,
    MAX_TOKENS,
    PROMPT_TEMPLATE,
    _CoderToolBackend,
    apply_file_blocks,
    sprint_report_path,
)
from loop_engine.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)

# Re-exported for tests/back-compat: the prompt parity test and any importer
# that referenced these on the persona module keep working after the extraction.
__all__ = ["CoderIacPersona", "PROMPT_TEMPLATE", "DEFAULT_MODEL", "MAX_TOKENS"]


class CoderIacPersona(BasePersona):
    consumes = ("architecture_definition", "sprint_plans")
    produces = ("implementation_reports",)

    def run(self, state: State, llm_client, findings: list[str] | None = None) -> State:
        architecture_definition = state.artifacts["architecture_definition"]
        sprint_blocks = json.loads(state.artifacts["sprint_plans"])

        try:
            reports: dict[str, str] = json.loads(
                state.artifacts.get("implementation_reports", "{}")
            )
        except json.JSONDecodeError:
            reports = {}

        questions = list(state.questions)
        existing_texts = {q.text for q in questions}

        # Sprints whose escalated questions were answered, plus sprints a
        # gate finding names by path (the evidence gate prefixes its findings
        # with the blamed sprint), are the only completed sprints worth
        # paying to redo on a findings pass. When findings arrive with no
        # attribution at all, fall back to redoing every sprint — re-running
        # nothing would return an identical artifact and trip the engine's
        # identical-findings escalation.
        resolved_sprints = {
            q.origin_detail
            for q in state.questions
            if q.origin_stage == "CoderIacPersona"
            and q.resolution is not None
            and q.origin_detail is not None
        }
        findings_sprints = {
            path for path in reports if any(path in finding for finding in findings or [])
        }
        targeted_sprints = resolved_sprints | findings_sprints

        # Inner loop: one invocation per sprint, in plan order. Sprints whose
        # reports already exist (a prior attempt, resumed run, or re-entry
        # after question resolution) are skipped unless findings target them.
        tool_backend = _CoderToolBackend()
        try:
            for block in sprint_blocks:
                sprint_path = block["path"]
                if sprint_path in reports:
                    rerun = bool(findings) and (
                        sprint_path in targeted_sprints or not targeted_sprints
                    )
                    if not rerun:
                        continue

                # Stable prefix (cached): template + architecture definition,
                # byte-identical across every sprint invocation in this inner
                # loop, so sprints 2..N read the prefix from cache. The sprint
                # plan and findings are volatile and stay in the user turns.
                system_blocks = [
                    PROMPT_TEMPLATE,
                    f"Architecture Definition Document:\n\n{architecture_definition}",
                ]
                initial_prompt = f"Sprint Plan ({sprint_path}):\n\n{block['content']}"

                previous_report = reports.get(sprint_path, "")
                if findings and previous_report.strip() and sections.has_sections(previous_report):
                    # Targeted revision: the sprint's prior report is an assistant
                    # turn; only the corrected sections come back, merged locally.
                    feedback = "\n".join(f"- {finding}" for finding in findings)
                    response = llm_client.call_messages(
                        [
                            {"role": "user", "content": initial_prompt},
                            {"role": "assistant", "content": previous_report},
                            {
                                "role": "user",
                                "content": (
                                    "Resolutions to your escalated questions:\n"
                                    f"{feedback}\n\n"
                                    "Return ONLY the corrected sections of your "
                                    "report, reproducing their `##`/`###` headers "
                                    "verbatim."
                                ),
                            },
                        ],
                        model=DEFAULT_MODEL,
                        max_tokens=MAX_TOKENS,
                        system_blocks=system_blocks,
                    )
                    report = sections.merge(previous_report, response.text).strip()
                else:
                    prompt = initial_prompt
                    if findings:
                        feedback = "\n".join(f"- {finding}" for finding in findings)
                        prompt += f"\n\n---\n\nResolutions to your escalated questions:\n{feedback}"
                    # Agentic implementation: the model reads prior sprints'
                    # output and runs the tests itself before finishing; the
                    # client debits budget per iteration.
                    tools, execute = tool_backend.resolve()
                    response = llm_client.run_tool_loop(
                        [{"role": "user", "content": prompt}],
                        model=DEFAULT_MODEL,
                        max_tokens=MAX_TOKENS,
                        tools=tools,
                        execute=execute,
                        system_blocks=system_blocks,
                    )
                    report = response.text.strip()
                if not report:
                    logger.warning("empty implementation response for %s", sprint_path)
                    continue

                # Apply the report's file blocks to the artifact tree (the tool
                # set is read/execute-only; all writes go through write_artifact).
                # Failures are recorded on the report so the gate can demand
                # corrected blocks with exact sprint attribution.
                failures = apply_file_blocks(report)
                if failures:
                    failure_lines = "\n".join(f"- {failure}" for failure in failures)
                    report += f"\n\n{EDIT_FAILURES_HEADER}\n\n{failure_lines}"

                reports[sprint_path] = report

                report_path = sprint_report_path(sprint_path)
                if report_path is not None:
                    try:
                        write_artifact(report, report_path)
                    except ValueError:
                        logger.warning("skipping report with invalid path %r", report_path)

                sprint_questions = [
                    q.model_copy(update={"origin_detail": sprint_path})
                    for q in extract_open_questions(report, "CoderIacPersona")
                ]
                new_questions = [q for q in sprint_questions if q.text not in existing_texts]
                questions.extend(new_questions)
                existing_texts.update(q.text for q in new_questions)
                if new_questions:
                    # Blocked on answers: stop burning budget on later sprints
                    # that likely depend on this one; the engine escalates and
                    # re-enters here with resolutions.
                    break
        finally:
            tool_backend.close()

        artifacts = {**state.artifacts, "implementation_reports": json.dumps(reports)}
        return state.model_copy(update={"artifacts": artifacts, "questions": questions})
