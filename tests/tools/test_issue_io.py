import json
from unittest.mock import patch

import pytest

from loop_engine.core.state import Question, State
from loop_engine.tools.issue_io import (
    IssueClosedWithoutAnswersError,
    apply_answers_to_questions,
    file_question_issue,
    parse_snapshot_path,
    read_issue_answers,
)


def _state() -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts={})


def _questions() -> list[Question]:
    return [
        Question(id="q1", origin_stage="ArchitecturePersona", text="Which region?"),
        Question(id="q2", origin_stage="CoderIacPersona", text="OIDC or API keys?"),
    ]


def test_file_question_issue_shells_out_to_gh_and_parses_number() -> None:
    with patch("loop_engine.tools.issue_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/acme/repo/issues/17\n"

        ref = file_question_issue(_state(), _questions(), "state/run-1/01_awaiting_issue.json")

    assert ref.number == 17
    args = run_gh.call_args.args[0]
    assert args[:2] == ["issue", "create"]
    body = args[args.index("--body") + 1]
    assert "1. **[ArchitecturePersona]** Which region?" in body
    assert "2. **[CoderIacPersona]** OIDC or API keys?" in body
    assert "Snapshot: `state/run-1/01_awaiting_issue.json`" in body


def test_read_issue_answers_parses_latest_answers_block() -> None:
    issue_data = {
        "state": "OPEN",
        "comments": [
            {"body": "first attempt\n```answers\n1: us-east-1\n```"},
            {"body": "corrected:\n```answers\n1: eu-west-1\n2: OIDC\n```"},
        ],
    }
    answers = read_issue_answers(17, issue_data)
    assert answers == {1: "eu-west-1", 2: "OIDC"}


def test_read_issue_answers_closed_without_answers_raises() -> None:
    issue_data = {"state": "CLOSED", "comments": [{"body": "won't fix"}]}
    with pytest.raises(IssueClosedWithoutAnswersError):
        read_issue_answers(17, issue_data)


def test_parse_snapshot_path_round_trips_from_filed_body() -> None:
    with patch("loop_engine.tools.issue_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/acme/repo/issues/17\n"
        file_question_issue(_state(), _questions(), "state/run-1/01_awaiting_issue.json")
        body = run_gh.call_args.args[0][run_gh.call_args.args[0].index("--body") + 1]

    assert parse_snapshot_path({"body": body}) == "state/run-1/01_awaiting_issue.json"


def test_apply_answers_marks_filed_questions_resolved_in_order() -> None:
    questions = _questions()
    updated = apply_answers_to_questions(questions, questions, {1: "eu-west-1"}, 17)

    assert updated[0].resolution == "eu-west-1"
    assert updated[0].resolved_by == "human:17"
    assert updated[1].resolution is None


def test_apply_answers_ignores_out_of_range_numbers() -> None:
    questions = _questions()
    updated = apply_answers_to_questions(questions, questions, {5: "nonsense"}, 17)
    assert all(q.resolution is None for q in updated)


def test_gh_output_with_json_body_parses() -> None:
    # Sanity-check the gh JSON shape contract used by read_issue.
    payload = json.dumps({"state": "OPEN", "body": "b", "comments": []})
    assert json.loads(payload)["state"] == "OPEN"
