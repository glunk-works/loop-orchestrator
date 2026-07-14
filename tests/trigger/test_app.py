import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from loop_engine.trigger.app import create_app
from loop_engine.trigger.parse import RunRequest

_SECRET = "test-webhook-secret-not-a-real-credential"

_LABELED_PAYLOAD = {
    "action": "labeled",
    "label": {"name": "agent-action"},
    "issue": {"number": 1, "title": "t", "body": "b"},
    "repository": {"full_name": "acme/widgets"},
}

_COMMENT_PAYLOAD = {
    "action": "created",
    "comment": {"body": "/agent-run"},
    "issue": {"number": 2, "title": "t2", "body": "b2"},
    "repository": {"full_name": "acme/widgets"},
}


class _FakeDispatcher:
    def __init__(self) -> None:
        self.received: list[RunRequest] = []

    async def dispatch(self, request: RunRequest) -> None:
        self.received.append(request)


def _sign(body: bytes, secret: str = _SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _client(monkeypatch) -> tuple[TestClient, _FakeDispatcher]:
    monkeypatch.setenv("LOOP_ENGINE_WEBHOOK_SECRET", _SECRET)
    fake = _FakeDispatcher()
    app = create_app(dispatcher=fake)
    return TestClient(app), fake


def _post(client: TestClient, event_name: str, payload: dict, *, signed: bool = True):
    body = json.dumps(payload).encode()
    headers = {"X-GitHub-Event": event_name}
    if signed:
        headers["X-Hub-Signature-256"] = _sign(body)
    return client.post("/webhook", content=body, headers=headers)


def test_labeled_agent_action_delivery_dispatches_and_returns_202(monkeypatch) -> None:
    client, fake = _client(monkeypatch)

    resp = _post(client, "issues", _LABELED_PAYLOAD)

    assert resp.status_code == 202
    assert len(fake.received) == 1
    assert fake.received[0].human_input == "t\n\nb"


def test_slash_command_comment_delivery_dispatches_and_returns_202(monkeypatch) -> None:
    client, fake = _client(monkeypatch)

    resp = _post(client, "issue_comment", _COMMENT_PAYLOAD)

    assert resp.status_code == 202
    assert len(fake.received) == 1
    assert fake.received[0].human_input == "t2\n\nb2"


def test_ping_and_unrelated_events_are_no_ops(monkeypatch) -> None:
    client, fake = _client(monkeypatch)

    resp = _post(client, "ping", {"zen": "hi"})

    assert resp.status_code == 204
    assert fake.received == []


def test_wrong_signature_is_rejected_and_not_dispatched(monkeypatch) -> None:
    client, fake = _client(monkeypatch)
    body = json.dumps(_LABELED_PAYLOAD).encode()

    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "issues", "X-Hub-Signature-256": "sha256=" + "0" * 64},
    )

    assert resp.status_code == 401
    assert fake.received == []


def test_missing_signature_is_rejected(monkeypatch) -> None:
    client, fake = _client(monkeypatch)

    resp = _post(client, "issues", _LABELED_PAYLOAD, signed=False)

    assert resp.status_code == 401
    assert fake.received == []


def test_tampered_body_fails_signature_check(monkeypatch) -> None:
    client, fake = _client(monkeypatch)
    body = json.dumps(_LABELED_PAYLOAD).encode()
    signature = _sign(body)
    tampered = body + b" "

    resp = client.post(
        "/webhook",
        content=tampered,
        headers={"X-GitHub-Event": "issues", "X-Hub-Signature-256": signature},
    )

    assert resp.status_code == 401
    assert fake.received == []


def test_valid_signature_over_exact_raw_body_passes(monkeypatch) -> None:
    client, fake = _client(monkeypatch)
    body = json.dumps(_LABELED_PAYLOAD).encode()
    signature = _sign(body)

    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "issues", "X-Hub-Signature-256": signature},
    )

    assert resp.status_code == 202
    assert len(fake.received) == 1


def test_signed_but_unparseable_body_returns_400_not_500(monkeypatch) -> None:
    client, fake = _client(monkeypatch)
    body = b"payload=%7Bnot+json%7D"
    signature = _sign(body)

    resp = client.post(
        "/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    assert resp.status_code == 400
    assert fake.received == []


def test_construct_app_without_secret_raises(monkeypatch) -> None:
    monkeypatch.delenv("LOOP_ENGINE_WEBHOOK_SECRET", raising=False)

    with pytest.raises(RuntimeError):
        create_app()


def test_health_endpoint_returns_200(monkeypatch) -> None:
    client, _ = _client(monkeypatch)

    resp = client.get("/health")

    assert resp.status_code == 200
