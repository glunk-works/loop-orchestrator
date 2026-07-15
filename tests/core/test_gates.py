import json

from loop_engine.core.gates import (
    ArtifactGate,
    GateDecision,
    extract_open_questions,
)
from loop_engine.core.state import Question, State


def _state(artifacts: dict[str, str], questions: list[Question] | None = None) -> State:
    return State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts=artifacts,
        questions=questions or [],
    )


def test_gate_revises_on_missing_artifact() -> None:
    result = ArtifactGate("doc")(_state({}), "SomeStage")
    assert result.decision is GateDecision.REVISE
    assert "missing or empty" in result.findings[0]


def test_gate_revises_on_unparseable_json() -> None:
    result = ArtifactGate("spec", parse_json="object")(_state({"spec": "not json"}), "S")
    assert result.decision is GateDecision.REVISE


def test_gate_revises_on_empty_parse_when_required() -> None:
    gate = ArtifactGate("plans", parse_json="list", require_nonempty_parse=True)
    result = gate(_state({"plans": "[]"}), "S")
    assert result.decision is GateDecision.REVISE
    assert "empty" in result.findings[0]


def test_gate_accepts_valid_document() -> None:
    result = ArtifactGate("doc")(_state({"doc": "# Architecture\n\nA real document."}), "S")
    assert result.decision is GateDecision.ACCEPT


def test_gate_escalates_question_shaped_output() -> None:
    """The exact old-pipeline failure: the model asks instead of delivering."""
    result = ArtifactGate("doc")(
        _state({"doc": "Before I proceed, what is your data residency requirement?"}), "S"
    )
    assert result.decision is GateDecision.ESCALATE
    assert result.questions[0].text.endswith("requirement?")


def test_gate_escalates_open_questions_section() -> None:
    doc = "# Doc\n\ncontent\n\n## Open Questions\n\n1. OIDC or API keys?\n2. Which region?"
    result = ArtifactGate("doc")(_state({"doc": doc}), "S")
    assert result.decision is GateDecision.ESCALATE
    assert [q.text for q in result.questions] == ["OIDC or API keys?", "Which region?"]


def test_gate_does_not_reescalate_answered_questions() -> None:
    doc = "# Doc\n\n## Open Questions\n\n1. Which region?"
    answered = Question(
        id="q1", origin_stage="S", text="Which region?", resolution="EU", resolved_by="pm"
    )
    result = ArtifactGate("doc")(_state({"doc": doc}, questions=[answered]), "S")
    assert result.decision is GateDecision.ACCEPT


def test_gate_escalates_pending_state_questions_for_stage() -> None:
    pending = Question(id="q1", origin_stage="S", text="Unresolvable field?")
    result = ArtifactGate("spec", parse_json="object")(
        _state({"spec": json.dumps({"a": "b"})}, questions=[pending]), "S"
    )
    assert result.decision is GateDecision.ESCALATE
    assert result.questions == [pending]


def test_extract_open_questions_stops_at_next_header() -> None:
    text = "## Open Questions\n\n1. One?\n- Two?\n\n## Next Section\n\n3. Not a question item"
    questions = extract_open_questions(text, "S")
    assert [q.text for q in questions] == ["One?", "Two?"]


def test_extract_open_questions_absent_section_returns_empty() -> None:
    assert extract_open_questions("# Doc with no questions", "S") == []


def test_gate_escalates_question_shaped_output_at_length_one_boundary() -> None:
    # Real boundary gap (Sprint 38 T3, BL-23): lower bound is `0 < len(stripped)`,
    # so a bare length-1 question-shaped string ("?") must still escalate.
    result = ArtifactGate("doc")(_state({"doc": "?"}), "S")
    assert result.decision is GateDecision.ESCALATE


def test_gate_escalates_question_shaped_output_at_max_length_boundary() -> None:
    # Real boundary gap: upper bound is `<= _QUESTION_SHAPED_MAX_LENGTH` (600),
    # so a question-shaped string of EXACTLY 600 chars must still escalate.
    doc = "a" * 599 + "?"
    assert len(doc) == 600
    result = ArtifactGate("doc")(_state({"doc": doc}), "S")
    assert result.decision is GateDecision.ESCALATE


def test_gate_escalates_question_shaped_output_with_trailing_markdown_emphasis() -> None:
    # Real gap: `.rstrip("*_`")` exists to strip trailing markdown emphasis
    # (e.g. a model bolding its own question) before checking for "?".
    result = ArtifactGate("doc")(
        _state({"doc": "Before I proceed, what is the target region?**"}), "S"
    )
    assert result.decision is GateDecision.ESCALATE
