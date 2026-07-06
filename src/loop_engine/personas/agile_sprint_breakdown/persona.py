import json
import logging
import re

from loop_engine.core.gates import extract_open_questions
from loop_engine.core.state import State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"
# A multi-sprint breakdown is several pages of structured markdown; the old
# 1024 default guaranteed silent truncation.
MAX_TOKENS = 8192

_FILEPATH_HEADER_RE = re.compile(r"^### FILEPATH:\s*(\S+)\s*$", re.MULTILINE)

# Embedded verbatim from prompts/03_agile_sprint_breakdown_prompt.md.
# tests/personas/test_prompt_parity.py guards against this drifting from
# that source file.
PROMPT_TEMPLATE = """# PROMPT DEFINITION

## ROLE

You are an Expert Senior Software Engineer, Agile Project Manager, and DevSecOps Practitioner.

## OBJECTIVE

Analyze the provided project specification and systematically decompose it into actionable,
security-conscious implementation sprints. Your output must be rigidly structured so that a
downstream autonomous AI coding agent can read, interpret, and execute each sprint without
ambiguity.

## INPUT CONTEXT

**Attached Specification Document:** [SPECIFICATION_DOCUMENT]
*(Read and analyze the attached file completely before beginning your breakdown.)*

## TASK INSTRUCTIONS

1. **Security Analysis:** Before decomposing, identify all security-relevant components in the
specification: data flows that cross trust boundaries, authentication and authorization surfaces,
external integrations, sensitive data handled, and any compliance requirements. You will use this
analysis to populate the `Security Considerations` field of each sprint.

2. **Analyze:** Review the attached specification to understand the core architecture, features,
and technical requirements. Identify all external dependencies and integration points.

3. **Decompose:** Break the project down into logical, sequential Agile sprints. Apply the
following ordering rules:
   - **Early sprints** establish foundational architecture, CI/CD pipeline setup, and security
tooling (linting, static analysis, secrets scanning). Do not defer these to later sprints.
   - **Middle sprints** implement features and integrations.
   - **Final sprints** address observability, performance, and hardening. Do not use vague terms
like "polish" or "cleanup" — name sprints by what they actually deliver.

4. **Atomicity:** Every task must represent a single, bounded unit of work that an autonomous
agent can complete in one pass. Tasks must not have ambiguous scope or open-ended research
requirements.

5. **Structure Output:** Format each sprint as a self-contained file at the specified path. Begin
your output with a single `GLOBAL DEFINITION OF DONE` block, followed by all sprint files.

## OUTPUT CONSTRAINTS

- Each sprint file path must follow the format:
`/sprints/[sprint_number]_[sprint_name]/sprint_plan.md` (e.g.,
`/sprints/01_ci_cd_foundation/sprint_plan.md`).
- Sprint names must be concrete and descriptive. Banned terms: `polish`, `cleanup`, `misc`,
`other`. Use precise terms: `observability`, `hardening`, `performance`, `documentation`,
`integration`.
- Use definitive language throughout. Never use "maybe", "should", "consider", or "might".
- Every sprint must include at least one task that directly addresses security concerns scoped to
that sprint's work.
- Each task description must define a single, bounded, atomic deliverable — not a category of work.
- Provide the output in the exact markdown structure shown below.

## REQUIRED OUTPUT FORMAT

Begin with this block, generated once:

---

## GLOBAL DEFINITION OF DONE

*[Generate this section from the specification. List the universal quality gates that every sprint
must satisfy before it is marked complete. Include conditions covering: test pass requirements,
linter/formatter compliance, no hardcoded secrets, dependency vulnerability scan result, CI
pipeline status, and any project-specific gates derived from the spec.]*

---

Then repeat the following template for each sprint:

### FILEPATH: /sprints/[sprint_number]_[sprint_name]/sprint_plan.md

**Sprint Goal:** [One sentence defining the objective of this sprint]

**Dependencies:** [None | List of specific prior sprints required to start this one]

**Security Considerations:** [Identify the threat surface introduced or touched by this sprint.
List specific mitigations, secure coding requirements, or scanning tasks that apply to this
sprint's scope. This field is mandatory on every sprint.]

**Risks & Blockers:** [List known unknowns, external dependencies, or failure modes that could
block this sprint. If none are identified, state "None identified."]

**Tasks:**

- **Task 1: [Task Name]**
  - **Description:** [Specific, atomic implementation details. Define exactly what is built,
configured, or changed — not a category of work.]
  - **Target Files:** [List of files to be created or modified]
  - **Acceptance Criteria:** [Testable conditions specific to this task that prove it is complete,
in addition to the Global Definition of Done]

- **Task 2: [Task Name]**
  - **Description:** [Specific, atomic implementation details. Define exactly what is built,
configured, or changed — not a category of work.]
  - **Target Files:** [List of files to be created or modified]
  - **Acceptance Criteria:** [Testable conditions specific to this task that prove it is complete,
in addition to the Global Definition of Done]

---
[Repeat this structure for all necessary sprints until the specification is fully covered]

## OPEN QUESTIONS

You operate in a non-interactive batch pipeline — you cannot ask and wait. If the architecture
definition is missing information you need to produce a correct breakdown, append a section
titled `## Open Questions` after the final sprint file: a numbered list, one self-contained
question per line. Still produce sprints for everything the questions do not block. Omit the
section entirely when there are none.
"""


def _parse_sprint_blocks(text: str) -> list[dict[str, str]]:
    matches = list(_FILEPATH_HEADER_RE.finditer(text))
    blocks = []
    for i, match in enumerate(matches):
        path = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        # Drop the "---" divider the output format places between sprint
        # files; it belongs to the response framing, not the file content.
        if content.endswith("\n---"):
            content = content[: -len("\n---")].rstrip()
        blocks.append({"path": path, "content": content})
    return blocks


class AgileSprintBreakdownPersona(BasePersona):
    consumes = ("architecture_definition",)
    produces = ("sprint_plans",)

    def run(self, state: State, llm_client, findings: list[str] | None = None) -> State:
        architecture_definition = state.artifacts["architecture_definition"]

        prompt = (
            f"{PROMPT_TEMPLATE}\n\n---\n\n"
            f"Architecture Definition Document:\n\n{architecture_definition}"
        )
        if findings:
            feedback = "\n".join(f"- {finding}" for finding in findings)
            prompt += (
                "\n\n---\n\nRevision feedback on your previous attempt — "
                f"address every item:\n{feedback}"
            )

        response = llm_client.call(prompt, model=DEFAULT_MODEL, max_tokens=MAX_TOKENS)
        sprint_blocks = _parse_sprint_blocks(response.text)

        # The gate only sees the parsed-blocks JSON artifact, so open
        # questions must be captured from the raw response here.
        existing_texts = {q.text for q in state.questions}
        questions = [
            *state.questions,
            *[
                q
                for q in extract_open_questions(response.text, "AgileSprintBreakdownPersona")
                if q.text not in existing_texts
            ],
        ]

        # The sprint plans are real deliverables, not just pipeline state:
        # write each one to its declared path. write_artifact validates the
        # path stays under an allowed root with no traversal; a model-invented
        # path that fails validation is skipped (and logged), never written.
        for block in sprint_blocks:
            try:
                write_artifact(block["content"], block["path"].lstrip("/"))
            except ValueError:
                logger.warning("skipping sprint block with invalid path %r", block["path"])

        artifacts = {**state.artifacts, "sprint_plans": json.dumps(sprint_blocks)}
        return state.model_copy(update={"artifacts": artifacts, "questions": questions})
