import pytest
from pydantic import ValidationError

from loop_engine.trigger.parse import RunRequest, parse_event


def _labeled_payload(label: str = "agent-action", action: str = "labeled") -> dict:
    return {
        "action": action,
        "label": {"name": label},
        "issue": {"number": 42, "title": "Add retries", "body": "Please add retry logic."},
        "repository": {"full_name": "acme/widgets"},
    }


def _comment_payload(body: str = "/agent-run", action: str = "created") -> dict:
    return {
        "action": action,
        "comment": {"body": body},
        "issue": {"number": 7, "title": "Fix flaky test", "body": "It flakes on CI."},
        "repository": {"full_name": "acme/widgets"},
    }


def test_labeled_agent_action_issue_yields_run_request() -> None:
    req = parse_event("issues", _labeled_payload())

    assert isinstance(req, RunRequest)
    assert req.human_input == "Add retries\n\nPlease add retry logic."
    assert req.repo_full_name == "acme/widgets"
    assert req.issue_number == 42


def test_slash_command_comment_yields_run_request() -> None:
    req = parse_event("issue_comment", _comment_payload())

    assert isinstance(req, RunRequest)
    assert req.human_input == "Fix flaky test\n\nIt flakes on CI."
    assert req.repo_full_name == "acme/widgets"
    assert req.issue_number == 7


def test_slash_command_matches_first_non_empty_line_stripped() -> None:
    req = parse_event("issue_comment", _comment_payload(body="\n  /agent-run  \n"))

    assert isinstance(req, RunRequest)


def test_missing_body_treated_as_empty() -> None:
    payload = _labeled_payload()
    payload["issue"]["body"] = None

    req = parse_event("issues", payload)

    assert req.human_input == "Add retries\n\n"


@pytest.mark.parametrize(
    "event_name,payload",
    [
        ("issues", _labeled_payload(label="bug")),
        ("issues", _labeled_payload(action="unlabeled")),
        ("issue_comment", _comment_payload(body="/agent-run please")),
        ("issue_comment", _comment_payload(body="not a command")),
        ("issue_comment", _comment_payload(action="edited")),
        ("ping", {"zen": "hello"}),
        ("issues", {"action": "opened"}),
    ],
)
def test_non_matching_events_are_no_ops(event_name, payload) -> None:
    assert parse_event(event_name, payload) is None


def test_malformed_payload_never_raises() -> None:
    assert parse_event("issues", {}) is None
    assert parse_event("issue_comment", {"action": "created"}) is None
    assert parse_event("issues", None) is None
    assert parse_event("issues", {"action": "labeled", "label": "not-a-dict"}) is None


def test_run_request_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        RunRequest(
            human_input="hi",
            repo_full_name="acme/widgets",
            issue_number=1,
            extra_field="nope",
        )


def test_run_request_coerces_typed_fields() -> None:
    req = RunRequest(
        human_input="hi",
        repo_full_name="acme/widgets",
        issue_number="1",
        budget_usd="2.5",
    )

    assert req.issue_number == 1
    assert req.budget_usd == 2.5
