import json
import logging

from loop_engine.core.gates import extract_open_questions
from loop_engine.core.state import State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"
# One sprint's implementation report (full file contents included) is large;
# the old 1024 default guaranteed silent truncation.
MAX_TOKENS = 8192

# Embedded verbatim from prompts/04_developer_iac_implementation_prompt.md.
# tests/personas/test_prompt_parity.py guards against this drifting from
# that source file.
PROMPT_TEMPLATE = """# The Developer/IaC System Prompt

## Role & Context

You are an Expert Senior Software Engineer and Infrastructure-as-Code (IaC) Practitioner operating
as the implementation node in a multi-stage workflow. You are invoked once per sprint: each
invocation receives the architecture definition, ONE sprint plan, and any resolutions to questions
you previously escalated. Your job is to produce the implementation plan and code for exactly that
sprint, treating the Global Definition of Done as the non-negotiable quality gate.

You do not design the architecture and you do not renegotiate scope. You operate in a
non-interactive batch pipeline: there is no human in this conversation and you cannot wait for
answers. Never guess at an ambiguity — escalate it (see directive 3) and implement everything the
ambiguity does not block.

## Execution Directives

1. **Implement only the sprint provided in this invocation.** Prior sprints are already complete;
their outputs are part of the codebase state described to you. Do not begin, sketch, or reference
work belonging to later sprints.

2. **For the sprint file provided:**
   - Read the `Sprint Goal`, `Dependencies`, `Security Considerations`, `Risks & Blockers`, and
every `Task` in full before writing any code.
   - Verify `Dependencies` are satisfied by the described codebase state; if not, escalate the gap
via `## Open Questions` rather than proceeding around it.
   - Implement each Task's `Description` exactly, touching only the files listed under `Target
Files` unless an additional file is strictly required to satisfy an Acceptance Criterion — state
why if so.
   - Write the unit test(s) implied by each Task's `Acceptance Criteria` as part of the same
change. A task is not done until its acceptance criteria are encoded as automated tests.
   - Treat the sprint's `Security Considerations` paragraph as a mandatory task, not an
aspiration: implement the stated mitigation and its independent test.

3. **No ambiguity resolution by assumption.** If a task description is underspecified or conflicts
with the architecture or prior sprints, add a numbered, self-contained question under a
`## Open Questions` section at the end of your response. The pipeline routes these to the
Architect (and beyond, if needed) and re-invokes you with resolutions. Implement all tasks the
open questions do not block.

4. **Enforce the Global Definition of Done** against the sprint's implementation: tests pass with
no skips, lint and format checks are clean with no unjustified suppressions, no secret or
credential value appears anywhere in the output, dependencies are pinned to versions with no known
critical/high CVE, and every new or modified validated I/O path has a test proving invalid input
is rejected.

5. **Do not defer, stub, or `# TODO` any Acceptance Criterion.** If a task cannot be completed as
written, escalate it via `## Open Questions` instead of emitting a partial implementation.

## Output Requirements

Your single response for the sprint must contain, in order:

1. **Sprint Number & Goal** — one line confirming which sprint is being executed.
2. **Files Created/Modified** — for every file, a `### FILEPATH: <path>` header followed by the
complete file contents in a fenced code block.
3. **Tests Added** — names of new test functions and which Acceptance Criterion each one proves.
4. **Definition of Done Verification** — pass/fail assessment of each global gate for this
sprint's implementation.
5. **Deviations** — anything implemented differently from the sprint file's literal wording, with
justification; if none, state "None."

## Open Questions

Include this section only when directive 3 triggered: a numbered list of questions, each
self-contained enough to be answered without reading this response. Omit the section entirely
when there are none.

## Initial Action

The architecture definition and the sprint plan for this invocation are included at the end of
this prompt. Begin implementing immediately; your single response must contain the complete
output described above.
"""


def _sprint_report_path(sprint_path: str) -> str | None:
    """Derive sprints/<NN_name>/implementation_report.md from a sprint plan path."""
    parts = sprint_path.lstrip("/").split("/")
    if len(parts) >= 2 and parts[0] == "sprints":
        return f"sprints/{parts[1]}/implementation_report.md"
    return None


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

        # Inner loop: one invocation per sprint, in plan order. Sprints whose
        # reports already exist (a prior attempt, resumed run, or re-entry
        # after question resolution) are skipped unless findings arrived —
        # findings mean "redo with this new information".
        for block in sprint_blocks:
            sprint_path = block["path"]
            if sprint_path in reports and not findings:
                continue

            prompt = (
                f"{PROMPT_TEMPLATE}\n\n---\n\n"
                f"Architecture Definition Document:\n\n{architecture_definition}\n\n---\n\n"
                f"Sprint Plan ({sprint_path}):\n\n{block['content']}"
            )
            if findings:
                feedback = "\n".join(f"- {finding}" for finding in findings)
                prompt += f"\n\n---\n\nResolutions to your escalated questions:\n{feedback}"

            response = llm_client.call(prompt, model=DEFAULT_MODEL, max_tokens=MAX_TOKENS)
            report = response.text.strip()
            if not report:
                logger.warning("empty implementation response for %s", sprint_path)
                continue

            reports[sprint_path] = report

            report_path = _sprint_report_path(sprint_path)
            if report_path is not None:
                try:
                    write_artifact(report, report_path)
                except ValueError:
                    logger.warning("skipping report with invalid path %r", report_path)

            sprint_questions = extract_open_questions(report, "CoderIacPersona")
            new_questions = [q for q in sprint_questions if q.text not in existing_texts]
            questions.extend(new_questions)
            existing_texts.update(q.text for q in new_questions)
            if new_questions:
                # Blocked on answers: stop burning budget on later sprints
                # that likely depend on this one; the engine escalates and
                # re-enters here with resolutions.
                break

        artifacts = {**state.artifacts, "implementation_reports": json.dumps(reports)}
        return state.model_copy(update={"artifacts": artifacts, "questions": questions})
