import json
import re
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from loop_engine.core.state import Question, State

_OPEN_QUESTIONS_HEADER_RE = re.compile(
    r"^#{1,6}\s+open questions\s*$", re.IGNORECASE | re.MULTILINE
)
_NUMBERED_ITEM_RE = re.compile(r"^\s*(?:\d+[.):]|[-*])\s+(.+?)\s*$")
_HEADER_LINE_RE = re.compile(r"^#{1,6}\s+\S")

# A response this short that ends in a question mark is the model asking us
# something, not delivering an artifact — the exact failure the old linear
# pipeline stored as ground truth.
_QUESTION_SHAPED_MAX_LENGTH = 600

# Prefix marking a finding that carries a resolved-question answer (as opposed
# to a gate status line). Shared with `engine._resolution_findings` so a
# self-looping persona (the Ralph Coder) can keep resolution answers in the
# prompt across iterations while trimming stale status lines.
RESOLUTION_FINDING_PREFIX = "Escalated question:"


class GateDecision(StrEnum):
    ACCEPT = "accept"
    REVISE = "revise"
    ESCALATE = "escalate"


@dataclass
class GateResult:
    decision: GateDecision
    findings: list[str] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)


def new_question(origin_stage: str, text: str) -> Question:
    return Question(id=uuid.uuid4().hex[:8], origin_stage=origin_stage, text=text)


def extract_open_questions(text: str, origin_stage: str) -> list[Question]:
    """Parse a '## Open Questions' section (any header level) into Questions.

    Items are numbered or bulleted lines; the section ends at the next header.
    """
    match = _OPEN_QUESTIONS_HEADER_RE.search(text)
    if match is None:
        return []

    questions: list[Question] = []
    for line in text[match.end() :].splitlines():
        if _HEADER_LINE_RE.match(line):
            break
        item = _NUMBERED_ITEM_RE.match(line)
        if item:
            questions.append(new_question(origin_stage, item.group(1)))
    return questions


def _is_question_shaped(text: str) -> bool:
    stripped = text.strip()
    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")


@dataclass(frozen=True)
class ArtifactGate:
    """Content gate for one produced artifact.

    Checks, in order: presence/non-emptiness, JSON shape (optional),
    question-shaped output, then extracts Open Questions for escalation.
    ACCEPT means "usable by the next stage", not merely "schema-valid State".
    """

    artifact_key: str
    parse_json: Literal["object", "list"] | None = None
    require_nonempty_parse: bool = False

    def __call__(self, state: State, stage_name: str) -> GateResult:
        raw = state.artifacts.get(self.artifact_key, "")
        if not raw.strip():
            return GateResult(
                GateDecision.REVISE,
                findings=[f"artifact {self.artifact_key!r} is missing or empty"],
            )

        if self.parse_json is not None:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                return GateResult(
                    GateDecision.REVISE,
                    findings=[f"artifact {self.artifact_key!r} is not valid JSON: {exc}"],
                )
            expected_type: type = dict if self.parse_json == "object" else list
            if not isinstance(parsed, expected_type):
                return GateResult(
                    GateDecision.REVISE,
                    findings=[
                        f"artifact {self.artifact_key!r} must be a JSON "
                        f"{self.parse_json}, got {type(parsed).__name__}"
                    ],
                )
            if self.require_nonempty_parse and not parsed:
                return GateResult(
                    GateDecision.REVISE,
                    findings=[
                        f"artifact {self.artifact_key!r} parsed to an empty {self.parse_json}"
                    ],
                )

        # A question whose text matches one already resolved has been
        # answered (the persona received the resolution as findings); only
        # genuinely new or still-pending texts escalate.
        answered_texts = {
            q.text
            for q in state.questions
            if q.origin_stage == stage_name and q.resolution is not None
        }
        all_extracted = extract_open_questions(raw, stage_name)
        extracted = [q for q in all_extracted if q.text not in answered_texts]
        if (
            not all_extracted  # an (answered) Open Questions section is not "asking"
            and self.parse_json is None
            and _is_question_shaped(raw)
            and raw.strip() not in answered_texts
        ):
            # No explicit Open Questions section, but the whole "artifact" is
            # a short text ending in a question mark: the model asked us
            # something instead of delivering. Escalate it as the question.
            return GateResult(
                GateDecision.ESCALATE,
                questions=[new_question(stage_name, raw.strip())],
            )

        pending = [
            q for q in state.questions if q.origin_stage == stage_name and q.resolution is None
        ]
        open_questions = pending + [q for q in extracted if all(q.text != p.text for p in pending)]
        if open_questions:
            return GateResult(GateDecision.ESCALATE, questions=open_questions)

        return GateResult(GateDecision.ACCEPT)
