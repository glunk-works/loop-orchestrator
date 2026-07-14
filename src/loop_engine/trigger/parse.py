"""Parse a GitHub webhook delivery into a `RunRequest`, or `None` (no-op).

Two bare-verb triggers carry no payload of their own — `human_input` is
always the issue's title+body. Everything else, including a malformed
payload, routes to `None` rather than raising: a webhook receiver must never
500 on an unrelated or misshapen delivery.
"""

from pydantic import BaseModel, ConfigDict, ValidationError

from loop_engine.runner import DEFAULT_BUDGET_USD

_LABEL_TRIGGER = "agent-action"
_SLASH_COMMAND = "/agent-run"


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    human_input: str
    budget_usd: float = DEFAULT_BUDGET_USD
    loop_name: str = "default"
    repo_full_name: str
    issue_number: int


def _is_agent_action_label(payload: dict) -> bool:
    try:
        return payload["action"] == "labeled" and payload["label"]["name"] == _LABEL_TRIGGER
    except (KeyError, TypeError):
        return False


def _is_agent_run_command(payload: dict) -> bool:
    try:
        if payload["action"] != "created":
            return False
        comment_body = payload["comment"]["body"]
    except (KeyError, TypeError):
        return False
    if not isinstance(comment_body, str):
        return False
    for line in comment_body.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped == _SLASH_COMMAND
    return False


def _build_request(payload: dict) -> "RunRequest | None":
    try:
        issue = payload["issue"]
        title = issue["title"]
        body = issue.get("body") or ""
        repo_full_name = payload["repository"]["full_name"]
        issue_number = issue["number"]
        return RunRequest(
            human_input=f"{title}\n\n{body}",
            repo_full_name=repo_full_name,
            issue_number=issue_number,
        )
    except (KeyError, TypeError, ValidationError):
        return None


def parse_event(event_name: str, payload: dict) -> "RunRequest | None":
    """The locked trigger grammar. Every non-matching or malformed delivery
    (including GitHub's `ping`) yields `None` — a safe no-op, never a raise."""
    if not isinstance(payload, dict):
        return None
    if event_name == "issues" and _is_agent_action_label(payload):
        return _build_request(payload)
    if event_name == "issue_comment" and _is_agent_run_command(payload):
        return _build_request(payload)
    return None
