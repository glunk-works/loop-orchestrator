import json
import logging
import re

from loop_engine.core.coder_gate import EDIT_FAILURES_HEADER
from loop_engine.core.gates import extract_open_questions
from loop_engine.core.state import State
from loop_engine.personas import sections
from loop_engine.personas.base import BasePersona
from loop_engine.tools.coder_tools import (
    READ_TOOL_SCHEMAS,
    grep,
    list_files,
    read_file,
    resolve_tool_path,
)
from loop_engine.tools.coder_tools.run_tests import RUN_TESTS_TOOL_SCHEMA, run_tests
from loop_engine.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)

CODER_TOOLS: list[dict] = [*READ_TOOL_SCHEMAS, RUN_TESTS_TOOL_SCHEMA]

_FILE_BLOCK_RE = re.compile(r"^### FILEPATH:\s*(\S+)\s*$", re.MULTILINE)
_SEARCH_REPLACE_RE = re.compile(
    r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", re.DOTALL
)
_FENCED_CODE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def _execute_tool(name: str, tool_input: dict) -> str:
    """Dispatch a model tool call to the read/execute-only coder tool set.

    File WRITES never happen here — the persona applies the model's output
    blocks through write_artifact after the loop finishes, keeping
    tools/state_io the sole writer.
    """
    if name == "read_file":
        return read_file(tool_input["path"])
    if name == "list_files":
        return list_files(tool_input["path"])
    if name == "grep":
        return grep(tool_input["pattern"], tool_input["path"])
    if name == "run_tests":
        return run_tests(tool_input["path"])
    raise ValueError(f"Unknown tool: {name!r}")


def _apply_file_blocks(report: str) -> list[str]:
    """Apply the report's `### FILEPATH:` blocks to the artifact tree.

    Two grammars per block: SEARCH/REPLACE edit pairs against an existing
    file, or a fenced code block holding complete file contents. Returns the
    failure descriptions for malformed or non-applying blocks — the caller
    records them so the gate can demand corrected blocks.
    """
    failures: list[str] = []
    matches = list(_FILE_BLOCK_RE.finditer(report))
    for index, match in enumerate(matches):
        path = match.group(1).lstrip("/")
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(report)
        region = report[start:end]

        try:
            pairs = _SEARCH_REPLACE_RE.findall(region)
            if pairs:
                target = resolve_tool_path(path)
                if not target.is_file():
                    failures.append(f"{path}: edit block targets a file that does not exist")
                    continue
                content = target.read_text(encoding="utf-8")
                applied = True
                for search, replace in pairs:
                    if search not in content:
                        failures.append(
                            f"{path}: SEARCH text not found in the current file: {search[:80]!r}"
                        )
                        applied = False
                        break
                    content = content.replace(search, replace, 1)
                if applied:
                    write_artifact(content, path)
                continue

            fence = _FENCED_CODE_RE.search(region)
            if fence is None:
                failures.append(
                    f"{path}: no fenced file contents or SEARCH/REPLACE edit block found"
                )
                continue
            write_artifact(fence.group(1), path)
        except ValueError as exc:
            failures.append(f"{path}: {exc}")
    return failures


DEFAULT_MODEL = "claude-sonnet-5"
# One sprint's implementation report (full file contents included) is large;
# the old 1024 default guaranteed silent truncation, and both 8192 and a
# subsequent 16000 proved insufficient for a real document in practice
# (TruncatedResponseError on real runs — see sprints/DEFERRED_VERIFICATION.md).
MAX_TOKENS = 64000

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

6. **Use your tools.** You can call `read_file`, `list_files`, and `grep` to inspect the current
codebase state (including prior sprints' outputs) and `run_tests` to execute the test suite. Read
before you write; never guess at a file's contents. Run the tests before claiming any acceptance
criterion is met — the pipeline re-runs them independently and rejects unverified claims.

## Output Requirements

Your single response for the sprint must contain, in order:

1. **Sprint Number & Goal** — one line confirming which sprint is being executed.
2. **Files Created/Modified** — for every file, a `### FILEPATH: <path>` header followed by
either (a) the complete file contents in a fenced code block (new files or full rewrites), or
(b) for targeted changes to an existing file, one or more edit blocks of the exact form:
<<<<<<< SEARCH
(text that exists in the current file, verbatim)
=======
(replacement text)
>>>>>>> REPLACE
The SEARCH text must match the current file exactly; the pipeline applies these blocks
mechanically and rejects any that do not apply.
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

The architecture definition is provided in the system context; the sprint plan for this
invocation is in the user message. Begin implementing immediately; your single response must
contain the complete output described above.

**Revision invocations:** when a prior version of your output is supplied as an assistant
turn together with revision feedback, return ONLY the corrected sections, reproducing their
headers verbatim; do not repeat unchanged sections.
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
        for block in sprint_blocks:
            sprint_path = block["path"]
            if sprint_path in reports:
                rerun = bool(findings) and (sprint_path in targeted_sprints or not targeted_sprints)
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
                response = llm_client.run_tool_loop(
                    [{"role": "user", "content": prompt}],
                    model=DEFAULT_MODEL,
                    max_tokens=MAX_TOKENS,
                    tools=CODER_TOOLS,
                    execute=_execute_tool,
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
            failures = _apply_file_blocks(report)
            if failures:
                failure_lines = "\n".join(f"- {failure}" for failure in failures)
                report += f"\n\n{EDIT_FAILURES_HEADER}\n\n{failure_lines}"

            reports[sprint_path] = report

            report_path = _sprint_report_path(sprint_path)
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

        artifacts = {**state.artifacts, "implementation_reports": json.dumps(reports)}
        return state.model_copy(update={"artifacts": artifacts, "questions": questions})
