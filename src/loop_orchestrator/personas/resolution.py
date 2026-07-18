"""Shared helpers for the resolver side of the escalation ladder.

A resolver persona (Architect for Coder questions, PM for anything below it)
prompts its LLM with its own artifact as context and gets back a JSON verdict
per question id; these helpers format the questions and apply the verdicts.
"""

import json

from loop_orchestrator.core.state import Question

VALID_IMPACTS = ("task", "plan", "architecture")


def format_questions(questions: list[Question]) -> str:
    return "\n".join(f"- {q.id}: {q.text}" for q in questions)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = stripped.split("\n", 1)[-1]
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    return stripped.strip()


def apply_resolution_response(
    text: str, questions: list[Question], resolved_by: str
) -> list[Question]:
    """Apply a resolver's JSON verdicts ({id: null | {resolution, impact}}).

    Unparseable output or malformed entries leave questions unresolved — an
    unanswerable question must escalate up the ladder, never silently vanish.
    """
    try:
        data = json.loads(_strip_code_fence(text))
    except json.JSONDecodeError:
        return questions
    if not isinstance(data, dict):
        return questions

    resolved: list[Question] = []
    for question in questions:
        verdict = data.get(question.id)
        if (
            isinstance(verdict, dict)
            and isinstance(verdict.get("resolution"), str)
            and verdict["resolution"].strip()
            and verdict.get("impact") in VALID_IMPACTS
        ):
            resolved.append(
                question.model_copy(
                    update={
                        "resolution": verdict["resolution"].strip(),
                        "impact": verdict["impact"],
                        "resolved_by": resolved_by,
                    }
                )
            )
        else:
            resolved.append(question)
    return resolved
