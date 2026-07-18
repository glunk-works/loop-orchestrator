"""Mode-agnostic Coder mechanics shared by the classic and Ralph personas.

Extracted verbatim from `coder_iac/persona.py` so both the per-sprint classic
Coder and the one-task-per-invocation Ralph Coder reuse the exact same tool
backend, edit-application, and prompt — no duplicated logic, no behavior change.
"""

import logging
import re
from pathlib import Path

from loop_orchestrator.tools.coder_tools import resolve_tool_path
from loop_orchestrator.tools.mcp import build_coder_tool_provider
from loop_orchestrator.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)

_FILE_BLOCK_RE = re.compile(r"^### FILEPATH:\s*(\S+)\s*$", re.MULTILINE)
_SEARCH_REPLACE_RE = re.compile(
    r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", re.DOTALL
)
_FENCED_CODE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

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
   - Scope every test to the Task's `Acceptance Criteria` as enumerated: cover exactly the
specified behavior and cases. Do not assert against private or underscore-prefixed module
internals, import mechanics, or other implementation details, and do not add tests for behavior
beyond what is specified.
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


class _CoderToolBackend:
    """The Coder's tool set, served over MCP.

    Tool execution runs in the server subprocess, out of the orchestrator
    process entirely — so under container/sandbox isolation the model's tools
    run sandboxed, which is the operating assumption `tools/coder_tools` is
    built on. (Phase 6 deleted the in-process dispatch this used to select
    between; there is no longer an unsandboxed path to fall back to.)

    The provider (which spawns the stdio server) is opened on first use and
    closed once.

    File WRITES never happen through these tools — they are read/execute-only.
    The persona applies the model's output blocks through `write_artifact`
    after the tool loop finishes, keeping `tools/state_io` the sole writer.
    """

    def __init__(self) -> None:
        self._provider = None

    def resolve(self):
        """Return (tools, execute) for a run_tool_loop call."""
        if self._provider is None:
            self._provider = build_coder_tool_provider(cwd=Path.cwd())
            self._provider.__enter__()
        return self._provider.tools, self._provider.execute

    def close(self) -> None:
        if self._provider is not None:
            self._provider.__exit__(None, None, None)
            self._provider = None


def apply_file_blocks(report: str) -> list[str]:
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


def sprint_report_path(sprint_path: str) -> str | None:
    """Derive sprints/<NN_name>/implementation_report.md from a sprint plan path."""
    parts = sprint_path.lstrip("/").split("/")
    if len(parts) >= 2 and parts[0] == "sprints":
        return f"sprints/{parts[1]}/implementation_report.md"
    return None
