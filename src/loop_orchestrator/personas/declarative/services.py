"""Shared services the `GeneratorNode` dispatches to, selected by config.

The genuinely-varying persona logic is a small registry of named strategies
along three axes — **input-wrappers**, **output-adapters**, **revision-styles**
— plus the `resolve_via_document` resolver. Each is factored from (and
behaviour-preserving against) the classic persona code so a declarative port is
byte-identical on the accept path. Unknown strategy names raise `ValueError`.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import get_args

from loop_orchestrator.core.gates import extract_open_questions
from loop_orchestrator.core.state import State
from loop_orchestrator.personas import sections
from loop_orchestrator.personas.agile_sprint_breakdown.manifest import build_task_manifest

# Reused verbatim from the classic personas so the declarative output is
# byte-identical — the parity guarantee, not a re-implementation.
from loop_orchestrator.personas.agile_sprint_breakdown.persona import _parse_sprint_blocks
from loop_orchestrator.personas.declarative.config import OutputAdapter, RevisionStyle
from loop_orchestrator.personas.pm.persona import (
    _parse_extraction_response,
    _wrap_untrusted_artifact,
)
from loop_orchestrator.personas.resolution import apply_resolution_response, format_questions
from loop_orchestrator.tools.state_io.writer import write_artifact

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# input-wrappers                                                              #
# --------------------------------------------------------------------------- #
def wrap_none(content: str, label: str) -> str:
    """Labelled input block, exactly the Architecture/Sprint cached-prefix form
    (`f"{label}:\\n\\n{content}"`)."""
    return f"{label}:\n\n{content}"


def wrap_untrusted(content: str, label: str) -> str:
    """The PM untrusted-document framing (label unused). Delegates to the classic
    `_wrap_untrusted_artifact` so the prompt-injection boundary bytes are equal."""
    return _wrap_untrusted_artifact(content)


INPUT_WRAPPERS: dict[str, Callable[[str, str], str]] = {
    "none": wrap_none,
    "untrusted": wrap_untrusted,
}


def get_input_wrapper(name: str) -> Callable[[str, str], str]:
    try:
        return INPUT_WRAPPERS[name]
    except KeyError:
        raise ValueError(
            f"unknown input-wrapper {name!r}; expected one of {tuple(INPUT_WRAPPERS)}"
        ) from None


# --------------------------------------------------------------------------- #
# output-adapters                                                             #
# --------------------------------------------------------------------------- #
# The section-merge revision instruction differs by adapter (the noun and the
# header token the model must reproduce verbatim); kept here beside the adapter.
_MARKDOWN_REVISION_INSTRUCTION = (
    "Return ONLY the corrected sections, reproducing their `##` headers verbatim."
)
_SPRINT_REVISION_INSTRUCTION = (
    "Return ONLY the corrected sprint files, reproducing their `### FILEPATH:` headers verbatim."
)

# Derived from config.OutputAdapter, the single source of truth for the legal
# strategy names (a Pydantic Literal already rejects anything else at config
# construction — this tuple is just for the error message here).
_OUTPUT_ADAPTERS = get_args(OutputAdapter)


def check_output_adapter(name: str) -> None:
    if name not in _OUTPUT_ADAPTERS:
        raise ValueError(f"unknown output-adapter {name!r}; expected one of {_OUTPUT_ADAPTERS}")


def revision_instruction(output_adapter: str) -> str:
    check_output_adapter(output_adapter)
    if output_adapter == "sprint_blocks":
        return _SPRINT_REVISION_INSTRUCTION
    return _MARKDOWN_REVISION_INSTRUCTION


def _extend_open_questions(state: State, raw_response: str, stage_name: str) -> list:
    existing = {q.text for q in state.questions}
    extracted = [
        q for q in extract_open_questions(raw_response, stage_name) if q.text not in existing
    ]
    return [*state.questions, *extracted]


def finalize_markdown(
    *,
    produces: str,
    effective_text: str,
    raw_response: str,
    extract_questions: bool,
    stage_name: str,
    state: State,
) -> State:
    artifacts = {**state.artifacts, produces: effective_text}
    update: dict[str, object] = {"artifacts": artifacts}
    if extract_questions:
        update["questions"] = _extend_open_questions(state, raw_response, stage_name)
    return state.model_copy(update=update)


def finalize_sprint_blocks(
    *,
    produces: str,
    effective_text: str,
    raw_response: str,
    stage_name: str,
    state: State,
) -> State:
    """The full classic `AgileSprintBreakdownPersona.run` tail: parse blocks,
    write each sprint file, emit `sprint_plans` + `task_manifest`, extract the
    Open Questions from the raw response."""
    sprint_blocks = _parse_sprint_blocks(effective_text)
    questions = _extend_open_questions(state, raw_response, stage_name)

    for block in sprint_blocks:
        try:
            write_artifact(block["content"], block["path"].lstrip("/"))
        except ValueError:
            logger.warning("skipping sprint block with invalid path %r", block["path"])

    manifest = build_task_manifest(sprint_blocks)
    artifacts = {
        **state.artifacts,
        produces: json.dumps(sprint_blocks),
        "task_manifest": json.dumps([task.model_dump() for task in manifest]),
    }
    return state.model_copy(update={"artifacts": artifacts, "questions": questions})


def parse_json_object(raw_response: str) -> dict[str, str]:
    """PM's extraction parse (fence-stripped JSON filtered to checklist fields).
    An unparseable response yields `{}` — never a partial/garbage spec."""
    return _parse_extraction_response(raw_response) or {}


def finalize_json_object(
    *,
    produces: str,
    parsed: dict[str, str],
    prior: dict[str, str],
    is_revision: bool,
    static_fields: dict[str, object],
    state: State,
) -> State:
    merged = {**prior, **parsed} if is_revision else dict(parsed)
    obj: dict[str, object] = {**merged, **static_fields}
    artifacts = {**state.artifacts, produces: json.dumps(obj)}
    return state.model_copy(update={"artifacts": artifacts})


# --------------------------------------------------------------------------- #
# revision-styles                                                            #
# --------------------------------------------------------------------------- #
# Derived from config.RevisionStyle — see _OUTPUT_ADAPTERS above.
_REVISION_STYLES = get_args(RevisionStyle)


def check_revision_style(name: str) -> None:
    if name not in _REVISION_STYLES:
        raise ValueError(f"unknown revision-style {name!r}; expected one of {_REVISION_STYLES}")


def format_feedback(findings: list[str]) -> str:
    """The bulleted feedback block shared by every revision-style / full regen."""
    return "\n".join(f"- {finding}" for finding in findings)


def merge_sections(prior_text: str, corrections: str) -> str:
    return sections.merge(prior_text, corrections)


# --------------------------------------------------------------------------- #
# resolver                                                                   #
# --------------------------------------------------------------------------- #
def resolve_via_document(
    *,
    document: str,
    document_var: str,
    template: str,
    resolved_by: str,
    model: str,
    max_tokens: int,
    questions: list,
    state: State,
    llm_client,
) -> list:
    """Answer escalated questions from an owned document — exactly the shape of
    `Architecture.resolve_questions` / `PM.resolve_questions`."""
    doc = state.artifacts.get(document, "")
    if not doc.strip():
        return questions
    prompt = template.format(**{"questions": format_questions(questions), document_var: doc})
    response = llm_client.call(prompt, model=model, max_tokens=max_tokens)
    return apply_resolution_response(response.text, questions, resolved_by=resolved_by)
