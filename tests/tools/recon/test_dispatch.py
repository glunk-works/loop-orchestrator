"""Hermetic tests for `ReconDispatcher` (T1, Q2 -- the real `gh` path gets
no live coverage until the V-run). `subprocess.run` is monkeypatched so
these never shell out for real: `GhReconDispatcher.dispatch`'s argv shape,
the S47-D8 token-correlation/S47-D9 bounded-poll logic in
`await_completion` (against a stubbed `gh run list` payload), and
`FakeReconDispatcher`'s canned round trip with zero subprocess calls.
"""

import json
import subprocess
import time

import pytest

from loop_orchestrator.tools.recon.dispatch import (
    DispatchHandle,
    FakeReconDispatcher,
    GhReconDispatcher,
    ReconDispatchFailedError,
    ReconTimeout,
)
from loop_orchestrator.tools.recon.models import ReconRequest


def _completed_process(argv: list[str], stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")


def test_dispatch_builds_a_fixed_argv_with_no_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((argv, kwargs))
        return _completed_process(argv, "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    dispatcher = GhReconDispatcher(repo="glunk-works/bounty-infra")
    request = ReconRequest(seed="acme.com", correlation_token="tok-abc")

    handle = dispatcher.dispatch(request)

    assert handle == DispatchHandle(correlation_token="tok-abc")
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[0] == "gh"
    assert kwargs.get("check") is True
    assert "shell" not in kwargs
    assert argv[1:3] == ["workflow", "run"]
    assert "--repo" in argv and "glunk-works/bounty-infra" in argv
    assert "seed=acme.com" in argv
    assert "token=tok-abc" in argv


def test_await_completion_polls_until_the_token_run_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        [],
        [{"displayTitle": "recon tok-xyz", "status": "in_progress", "conclusion": None}],
        [{"displayTitle": "recon tok-xyz", "status": "completed", "conclusion": "success"}],
    ]

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return _completed_process(argv, json.dumps(responses.pop(0)))

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    dispatcher = GhReconDispatcher(
        repo="glunk-works/bounty-infra", poll_interval_seconds=0, max_wait_seconds=60
    )
    key = dispatcher.await_completion(DispatchHandle(correlation_token="tok-xyz"))

    assert key == "recon/tok-xyz.jsonl"
    assert responses == []


def test_await_completion_raises_recon_timeout_when_nothing_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return _completed_process(argv, "[]")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    dispatcher = GhReconDispatcher(
        repo="glunk-works/bounty-infra", poll_interval_seconds=0, max_wait_seconds=0
    )
    with pytest.raises(ReconTimeout):
        dispatcher.await_completion(DispatchHandle(correlation_token="tok-none"))


def test_await_completion_raises_on_a_failed_run(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [{"displayTitle": "recon tok-bad", "status": "completed", "conclusion": "failure"}]

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return _completed_process(argv, json.dumps(payload))

    monkeypatch.setattr(subprocess, "run", fake_run)
    dispatcher = GhReconDispatcher(repo="glunk-works/bounty-infra", max_wait_seconds=60)

    with pytest.raises(ReconDispatchFailedError):
        dispatcher.await_completion(DispatchHandle(correlation_token="tok-bad"))


def test_fake_recon_dispatcher_never_shells_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("FakeReconDispatcher must not shell out")

    monkeypatch.setattr(subprocess, "run", boom)
    dispatcher = FakeReconDispatcher()
    request = ReconRequest(seed="acme.com", correlation_token="tok-fake")

    handle = dispatcher.dispatch(request)
    key = dispatcher.await_completion(handle)

    assert key == "recon/tok-fake.jsonl"


def test_fake_recon_dispatcher_honors_an_explicit_s3_key() -> None:
    dispatcher = FakeReconDispatcher(s3_key="recon/canned.jsonl")
    request = ReconRequest(seed="acme.com", correlation_token="tok-1")

    handle = dispatcher.dispatch(request)
    key = dispatcher.await_completion(handle)

    assert key == "recon/canned.jsonl"
