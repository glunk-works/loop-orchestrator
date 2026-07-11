"""PM behavior that outlives the classic `PMPersona` class.

Phase 6 deleted `PMPersona` (and its embedded extraction / followup /
resolution prompt templates — those now live in `prompts/`, which the
declarative `PMGenerator` config loads and which is the sole source of truth).

What remains here is the PM logic the declarative path still calls:

- `fold_answers` — folds a human's GitHub-issue answers back into the project
  spec and classifies each answer's blast radius. `PMGenerator.fold_answers`
  delegates to it, and `cli.resume` drives it after an issue round-trip. It has
  no declarative-config equivalent: it is a bespoke second LLM call, not a
  document-generation pass.
- `_wrap_untrusted_artifact` / `_parse_extraction_response` — reused verbatim by
  `personas/declarative/services.py`, so the generated output stays byte-identical
  to what the classic persona produced.
"""

import json
import logging

from loop_engine.core.state import State
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"
EXTRACTION_MAX_TOKENS = 4096

FOLD_ANSWERS_PROMPT_TEMPLATE = (
    "You are the PM persona and the owner of the project specification. A "
    "human answered previously escalated questions; fold their answers into "
    "the specification and classify each answer's blast radius: "
    '"task" (only the asking stage needs it), "plan" (the sprint breakdown '
    'must change), or "architecture" (the architecture definition must be '
    "revised).\n\n"
    "Respond with ONLY a JSON object of the shape "
    '{{"spec_updates": {{"<field>": "<new value>", ...}}, '
    '"impacts": {{"<question id>": "task" | "plan" | "architecture", ...}}}}. '
    "spec_updates may only use fields from this list: {fields}. Include an "
    "impact for every question id. No commentary, no code fences.\n\n"
    "Answered questions:\n{answers}\n\nCurrent Project Specification:\n\n{project_spec}"
)


def _wrap_untrusted_artifact(content: str) -> str:
    return f"<untrusted_artifact>\n{content}\n</untrusted_artifact>"


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = stripped.split("\n", 1)[-1]
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    return stripped.strip()


def _parse_extraction_response(text: str) -> dict[str, str] | None:
    """None means the response wasn't parseable JSON — the caller must treat
    that differently from a valid response that extracted nothing."""
    try:
        data = json.loads(_strip_code_fence(text))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    result: dict[str, str] = {}
    for field_name, value in data.items():
        if field_name not in CHECKLIST_FIELDS or not isinstance(value, str):
            continue
        stripped_value = value.strip()
        if stripped_value:
            result[field_name] = stripped_value
    return result


def fold_answers(state: State, llm_client) -> State:
    """Fold human-provided answers into the spec and classify impacts.

    Called on resume after a GitHub issue round-trip: questions arriving
    here have `resolution` set (by issue_io) but no `impact` yet.
    """
    answered = [q for q in state.questions if q.resolution is not None and q.impact is None]
    if not answered:
        return state

    answers_text = "\n".join(f"- {q.id}: {q.text}\n  answer: {q.resolution}" for q in answered)
    prompt = FOLD_ANSWERS_PROMPT_TEMPLATE.format(
        fields=", ".join(CHECKLIST_FIELDS),
        answers=answers_text,
        project_spec=state.artifacts.get("project_spec", "{}"),
    )
    # Unlike resolve_questions' terse resolution mapping, spec_updates can
    # rewrite full checklist field text (not just a short answer per
    # question) — sized like extraction, not like resolution.
    response = llm_client.call(prompt, model=DEFAULT_MODEL, max_tokens=EXTRACTION_MAX_TOKENS)

    try:
        data = json.loads(_strip_code_fence(response.text))
    except json.JSONDecodeError:
        data = {}
    spec_updates = data.get("spec_updates") if isinstance(data, dict) else {}
    impacts = data.get("impacts") if isinstance(data, dict) else {}
    if not isinstance(spec_updates, dict):
        spec_updates = {}
    if not isinstance(impacts, dict):
        impacts = {}

    artifacts = state.artifacts
    if spec_updates:
        try:
            spec = json.loads(state.artifacts.get("project_spec", "{}"))
        except json.JSONDecodeError:
            spec = {}
        for field_name, value in spec_updates.items():
            if field_name in CHECKLIST_FIELDS and isinstance(value, str):
                spec[field_name] = value
        artifacts = {**state.artifacts, "project_spec": json.dumps(spec)}

    questions = [
        q.model_copy(update={"impact": impacts[q.id]})
        if q in answered and impacts.get(q.id) in ("task", "plan", "architecture")
        # Default unclassified human answers to the broadest safe rework
        # scope below architecture: re-planning is wasteful but correct,
        # silently narrowing to "task" could skip required rework.
        else (q.model_copy(update={"impact": "plan"}) if q in answered else q)
        for q in state.questions
    ]
    return state.model_copy(update={"artifacts": artifacts, "questions": questions})
