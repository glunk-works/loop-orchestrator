import json
from unittest.mock import patch

import pytest

from loop_orchestrator.core.state import Question, State
from loop_orchestrator.tools.issue_io import (
    IssueClosedWithoutAnswersError,
    create_issue,
    parse_issue_answers,
    parse_snapshot_path,
    read_issue,
    render_question_issue,
)


def _state() -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts={})


def _questions() -> list[Question]:
    return [
        Question(id="q1", origin_stage="ArchitecturePersona", text="Which region?"),
        Question(id="q2", origin_stage="CoderIacPersona", text="OIDC or API keys?"),
    ]


def test_parse_issue_answers_parses_latest_answers_block() -> None:
    issue_data = {
        "state": "OPEN",
        "comments": [
            {"body": "first attempt\n```answers\n1: us-east-1\n```"},
            {"body": "corrected:\n```answers\n1: eu-west-1\n2: OIDC\n```"},
        ],
    }
    answers = parse_issue_answers(issue_data)
    assert answers == {1: "eu-west-1", 2: "OIDC"}


def test_parse_issue_answers_closed_without_answers_raises_bare() -> None:
    issue_data = {"state": "CLOSED", "comments": [{"body": "won't fix"}]}
    with pytest.raises(IssueClosedWithoutAnswersError):
        parse_issue_answers(issue_data)


def test_closed_without_answers_error_includes_issue_number() -> None:
    """R5: the issue number is folded back into the abort message."""
    issue_data = {"state": "CLOSED", "comments": []}
    with pytest.raises(IssueClosedWithoutAnswersError, match="#42"):
        parse_issue_answers(issue_data, 42)


def test_answers_block_quoted_in_a_reply_does_not_shadow_the_real_one() -> None:
    """R6: a human "Quote reply" that echoes the bot's own example block (a
    second ```answers block in the *same* comment) must not hide the real
    answers that follow it — `finditer`, not first-match `search`."""
    issue_data = {
        "state": "OPEN",
        "comments": [
            {
                "body": (
                    "> ```answers\n> 1: your answer\n> 2: your answer\n> ```\n\n"
                    "```answers\n1: eu-west-1\n2: OIDC\n```"
                )
            }
        ],
    }
    assert parse_issue_answers(issue_data) == {1: "eu-west-1", 2: "OIDC"}


def test_parse_snapshot_path_round_trips_from_filed_body() -> None:
    _, body, _ = render_question_issue(_state(), _questions(), "state/run-1/01_awaiting_issue.json")
    assert parse_snapshot_path({"body": body}) == "state/run-1/01_awaiting_issue.json"


def test_gh_output_with_json_body_parses() -> None:
    # Sanity-check the gh JSON shape contract used by read_issue.
    payload = json.dumps({"state": "OPEN", "body": "b", "comments": []})
    assert json.loads(payload)["state"] == "OPEN"


def test_render_question_issue_matches_filed_issue_body_byte_for_byte() -> None:
    state, questions = _state(), _questions()

    title, body, label = render_question_issue(
        state, questions, "state/run-1/01_awaiting_issue.json"
    )

    with patch("loop_orchestrator.tools.issue_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/acme/repo/issues/17\n"
        create_issue(title, body, label)
        args = run_gh.call_args.args[0]

    assert title == args[args.index("--title") + 1]
    assert body == args[args.index("--body") + 1]
    assert label == args[args.index("--label") + 1]


def test_create_issue_shells_expected_argv_and_parses_ref() -> None:
    with patch("loop_orchestrator.tools.issue_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/acme/repo/issues/42\n"
        ref = create_issue("t", "b", "l")

    run_gh.assert_called_once_with(
        ["issue", "create", "--title", "t", "--body", "b", "--label", "l"]
    )
    assert ref.number == 42
    assert ref.url == "https://github.com/acme/repo/issues/42"


def test_create_issue_forwards_explicit_repo_as_flag() -> None:
    """R8: an explicit `repo` becomes `--repo`, not left to gh's implicit
    cwd-derived resolution."""
    with patch("loop_orchestrator.tools.issue_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/acme/repo/issues/42\n"
        create_issue("t", "b", "l", repo="acme/repo")

    run_gh.assert_called_once_with(
        ["issue", "create", "--title", "t", "--body", "b", "--label", "l", "--repo", "acme/repo"]
    )


def test_read_issue_forwards_explicit_repo_as_flag() -> None:
    with patch("loop_orchestrator.tools.issue_io.github._run_gh") as run_gh:
        run_gh.return_value = json.dumps({"state": "OPEN", "body": "b", "comments": []})
        read_issue(42, repo="acme/repo")

    run_gh.assert_called_once_with(
        ["issue", "view", "42", "--json", "state,body,comments,url", "--repo", "acme/repo"]
    )
