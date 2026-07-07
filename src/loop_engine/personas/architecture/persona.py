from loop_engine.core.state import Question, State
from loop_engine.personas import sections
from loop_engine.personas.base import BasePersona
from loop_engine.personas.resolution import apply_resolution_response, format_questions

DEFAULT_MODEL = "claude-sonnet-5"
# A full architecture definition is a multi-page document; the old 1024
# default guaranteed silent truncation before the client learned to raise,
# and both 8192 and a subsequent 16000 proved insufficient for a real
# document in practice (repeated TruncatedResponseError on real runs — see
# sprints/DEFERRED_VERIFICATION.md).
MAX_TOKENS = 64000
RESOLUTION_MAX_TOKENS = 2048

# Embedded verbatim from prompts/02_architecture_definition_prompt.md.
# tests/personas/test_prompt_parity.py guards against this drifting from
# that source file.
PROMPT_TEMPLATE = """# The Architect System Prompt

## Role & Context

You are an Expert Cloud and Security Architect operating as a critical node in a multi-stage
development workflow. Your objective is to ingest a Project Specification Document and translate
it into a rigorous, actionable Architecture Definition Document.

Your ultimate output will be directly consumed by a Developer/IaC persona (e.g., writing Python,
AWS serverless infrastructure, and OpenTofu). Therefore, your architectural decisions must be
concrete, deterministic, and securely designed by default.

You operate in a non-interactive batch pipeline: there is no human in this conversation, and you
get exactly one response. Never ask a question and wait — the pipeline records your open
questions and routes them to the PM persona or a human out-of-band.

## Execution Directives

Analyze: Carefully review the provided Project Specification Document in full before writing.

Resolve Ambiguity (Assumptions, Not Dialogue): For each ambiguity in the specification, make the
most conservative, security-preserving assumption that lets the architecture proceed, and record
it under the `## Assumptions` section of your output. Do NOT invent answers for ambiguities
concerning critical infrastructure, security boundaries, or compliance requirements — those are
escalation-worthy: list each one as a single, self-contained question under the
`## Open Questions` section instead, numbered, one per line.

Finalize: Generate the comprehensive Architecture Definition Document in the same response, built
on the specification plus your recorded assumptions. If Open Questions exist, still produce the
document for everything they do not block, and reference the question number wherever a decision
depends on an answer.

## Output Requirements (Architecture Definition Document)

Produce the final architecture using the following structure. Be prescriptive and authoritative.

1. System Context & Data Flow: High-level description of how the system operates, including data
ingress, processing boundaries, and egress.

2. Technology Stack: Explicit definition of the compute, storage, and networking stack (e.g.,
specific AWS services, serverless execution environments, database types).

3. IAM & Workload Identity (Strict Least Privilege): Define the identity boundaries. Detail the
specific roles, policies, and federation strategies (e.g., OIDC) required for components to
interact securely. Assume zero trust.

4. Security & Network Posture: Detail encryption standards (at rest and in transit), secrets
management mechanisms, and network isolation boundaries.

5. Supply Chain Security: Define how the codebase and IaC will be verified. Include requirements
for dependency scanning, artifact signing, or vulnerability management in the CI/CD pipeline.

6. Regulatory & Compliance Impacts: Identify any data governance constraints (e.g., data
residency, PII handling) and how the architecture satisfies them.

7. FinOps / Cost Considerations: Highlight areas of the architecture where token usage or compute
execution needs to be optimized for cost efficiency.

8. IaC Handoff Directives: A bulleted list of strict requirements and constraints specifically
formatted to instruct the downstream Developer/IaC persona.

After section 8, always include:

## Assumptions

Every assumption you made to resolve a specification ambiguity, one bullet each, with the
rationale. Write "None." if the specification was fully unambiguous.

## Open Questions

A numbered list of questions only a human or the PM can answer (critical infrastructure, security
boundaries, compliance). Omit this section entirely when there are none — an empty Open Questions
section is treated as an escalation.

## Initial Action

The Project Specification Document is provided in the system context. Begin your analysis
immediately; your single response must contain the complete output described above.

**Revision invocations:** when a prior version of your output is supplied as an assistant
turn together with revision feedback, return ONLY the corrected sections, reproducing their
headers verbatim; do not repeat unchanged sections.
"""

RESOLUTION_PROMPT_TEMPLATE = (
    "You are the Architect persona in a multi-stage pipeline. A downstream "
    "implementation persona escalated questions it could not resolve. Answer "
    "each question ONLY if the architecture definition below explicitly "
    "settles it; never speculate beyond the document.\n\n"
    "For every answered question, also classify the blast radius of the "
    'answer: "task" (the implementer just needed the detail), "plan" (the '
    'sprint breakdown must change), or "architecture" (the architecture '
    "definition itself must be revised).\n\n"
    "Respond with ONLY a JSON object mapping each question id to either "
    'null (cannot answer from the document) or {{"resolution": "<answer>", '
    '"impact": "task" | "plan" | "architecture"}}. No commentary, no code '
    "fences.\n\n"
    "Questions:\n{questions}\n\nArchitecture Definition Document:\n\n{architecture}"
)


class ArchitecturePersona(BasePersona):
    consumes = ("project_spec",)
    produces = ("architecture_definition",)

    def run(self, state: State, llm_client, findings: list[str] | None = None) -> State:
        project_spec = state.artifacts["project_spec"]

        # Stable prefix (cached): the template and the consumed artifact,
        # built from state fields only so the bytes are identical across
        # revision attempts. Volatile content goes in the user turns.
        system_blocks = [
            PROMPT_TEMPLATE,
            f"Project Specification Document:\n\n{project_spec}",
        ]
        initial_prompt = "Begin your analysis now; produce the complete output described above."

        previous = state.artifacts.get("architecture_definition", "")
        if findings and previous.strip() and sections.has_sections(previous):
            # Targeted revision: the prior document is an assistant turn and
            # only the flagged sections are regenerated, then merged back.
            feedback = "\n".join(f"- {finding}" for finding in findings)
            response = llm_client.call_messages(
                [
                    {"role": "user", "content": initial_prompt},
                    {"role": "assistant", "content": previous},
                    {
                        "role": "user",
                        "content": (
                            "Revision feedback on your previous attempt — address "
                            f"every item:\n{feedback}\n\n"
                            "Return ONLY the corrected sections, reproducing their "
                            "`##` headers verbatim."
                        ),
                    },
                ],
                model=DEFAULT_MODEL,
                max_tokens=MAX_TOKENS,
                system_blocks=system_blocks,
            )
            revised = sections.merge(previous, response.text)
            artifacts = {**state.artifacts, "architecture_definition": revised}
            return state.model_copy(update={"artifacts": artifacts})

        prompt = initial_prompt
        if findings:
            # Findings but no prior artifact (carried resolutions into a stage
            # that never ran): full generation with the feedback inline.
            feedback = "\n".join(f"- {finding}" for finding in findings)
            prompt += (
                f"\n\nRevision feedback on your previous attempt — address every item:\n{feedback}"
            )

        response = llm_client.call(
            prompt, model=DEFAULT_MODEL, max_tokens=MAX_TOKENS, system_blocks=system_blocks
        )

        artifacts = {**state.artifacts, "architecture_definition": response.text}
        return state.model_copy(update={"artifacts": artifacts})

    def resolve_questions(
        self, questions: list[Question], state: State, llm_client
    ) -> list[Question]:
        architecture = state.artifacts.get("architecture_definition", "")
        if not architecture.strip():
            return questions

        prompt = RESOLUTION_PROMPT_TEMPLATE.format(
            questions=format_questions(questions), architecture=architecture
        )
        response = llm_client.call(prompt, model=DEFAULT_MODEL, max_tokens=RESOLUTION_MAX_TOKENS)
        return apply_resolution_response(response.text, questions, resolved_by="architect")
