import asyncio
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

from loop_orchestrator.slack_control.command import SlackRunCommand
from loop_orchestrator.slack_control.dispatch import SlackRunDispatcher


def _command(
    envelope_id: str = "env-1", human_input: str = "do it", channel_id: str = "C1"
) -> SlackRunCommand:
    return SlackRunCommand(
        human_input=human_input, budget_usd=5.00, channel_id=channel_id, envelope_id=envelope_id
    )


def _fake_state(status: str = "completed") -> MagicMock:
    state = MagicMock()
    state.status.value = status
    return state


def test_dispatch_invokes_runner_once_with_command_fields(monkeypatch) -> None:
    calls = []

    def fake_run_new(human_input, *, budget_usd, loop_name):
        calls.append((human_input, budget_usd, loop_name))
        return MagicMock()

    monkeypatch.setattr("loop_orchestrator.runner.run_new", fake_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_command(human_input="fix the bug", envelope_id="env-9"))
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == [("fix the bug", 5.00, "default")]


def test_dispatch_returns_before_the_run_finishes(monkeypatch) -> None:
    started = threading.Event()
    release = threading.Event()

    def fake_run_new(human_input, *, budget_usd, loop_name):
        started.set()
        assert release.wait(timeout=5), "test deadlocked waiting for release"
        return MagicMock()

    monkeypatch.setattr("loop_orchestrator.runner.run_new", fake_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> float:
        t0 = time.monotonic()
        await dispatcher.dispatch(_command())
        elapsed = time.monotonic() - t0
        release.set()
        await asyncio.sleep(0.2)
        return elapsed

    elapsed = asyncio.run(main())

    assert elapsed < 1.0


def test_second_dispatch_for_same_envelope_while_active_is_a_no_op(monkeypatch) -> None:
    entered = threading.Event()
    release = threading.Event()
    calls = []

    def fake_run_new(human_input, *, budget_usd, loop_name):
        calls.append(human_input)
        entered.set()
        assert release.wait(timeout=5), "test deadlocked waiting for release"
        return MagicMock()

    monkeypatch.setattr("loop_orchestrator.runner.run_new", fake_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_command(envelope_id="env-dup"))
        await asyncio.to_thread(entered.wait, 5)
        await dispatcher.dispatch(_command(envelope_id="env-dup"))
        await asyncio.sleep(0.1)
        release.set()
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == ["do it"]


def test_envelope_can_be_dispatched_again_after_run_completes(monkeypatch) -> None:
    calls = []

    def fake_run_new(human_input, *, budget_usd, loop_name):
        calls.append(human_input)
        return MagicMock()

    monkeypatch.setattr("loop_orchestrator.runner.run_new", fake_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_command(envelope_id="env-3"))
        await asyncio.sleep(0.2)
        await dispatcher.dispatch(_command(envelope_id="env-3"))
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == ["do it", "do it"]


def test_in_flight_task_is_strongly_referenced_and_released_on_completion(monkeypatch) -> None:
    entered = threading.Event()
    release = threading.Event()

    def fake_run_new(human_input, *, budget_usd, loop_name):
        entered.set()
        assert release.wait(timeout=5), "test deadlocked waiting for release"
        return MagicMock()

    monkeypatch.setattr("loop_orchestrator.runner.run_new", fake_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_command(envelope_id="env-11"))
        await asyncio.to_thread(entered.wait, 5)
        assert len(dispatcher._tasks) == 1
        release.set()
        await asyncio.sleep(0.2)
        assert len(dispatcher._tasks) == 0

    asyncio.run(main())


def test_dispatcher_serializes_concurrent_runs_for_different_envelopes(monkeypatch) -> None:
    """`os.chdir` inside `worktree_run` is still process-global (BL-8), so two
    *different* envelopes' runs must not actually execute concurrently -- the
    dispatcher lock makes that chdir race unreachable rather than merely
    unlikely, mirroring `InProcessDispatcher`'s serialization posture."""
    order = []
    release_first = threading.Event()

    def fake_run_new(human_input, *, budget_usd, loop_name):
        order.append(f"start:{human_input}")
        if human_input == "first":
            assert release_first.wait(timeout=5), "test deadlocked waiting for release"
        order.append(f"end:{human_input}")
        return MagicMock()

    monkeypatch.setattr("loop_orchestrator.runner.run_new", fake_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_command(envelope_id="env-a", human_input="first"))
        await dispatcher.dispatch(_command(envelope_id="env-b", human_input="second"))
        await asyncio.sleep(0.1)
        # "second" must not have started yet -- the lock is held by "first".
        assert order == ["start:first"]
        release_first.set()
        await asyncio.sleep(0.2)
        assert order == ["start:first", "end:first", "start:second", "end:second"]

    asyncio.run(main())


def test_run_failure_is_logged_and_releases_the_dedupe_key(monkeypatch, caplog) -> None:
    calls = []

    def failing_run_new(human_input, *, budget_usd, loop_name):
        calls.append(human_input)
        raise RuntimeError("boom")

    monkeypatch.setattr("loop_orchestrator.runner.run_new", failing_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        with caplog.at_level("ERROR", logger="loop_orchestrator.slack_control.dispatch"):
            await dispatcher.dispatch(_command(envelope_id="env-7"))
            await asyncio.sleep(0.2)
            await dispatcher.dispatch(_command(envelope_id="env-7"))
            await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == ["do it", "do it"]
    assert "run failed for envelope env-7" in caplog.text


def _resume_kwargs(**overrides) -> dict:
    defaults = dict(
        snapshot_path=Path("state/run-1/02_awaiting_slack.json"),
        resolved_answers={1: "yes"},
        budget_usd=5.00,
        envelope_id="env-resume-1",
        thread_ts="1700000000.000100",
        channel_id="C1",
    )
    return {**defaults, **overrides}


def test_dispatch_resume_loads_the_snapshot_and_calls_resume_run(monkeypatch) -> None:
    calls = []
    loaded_state = _fake_state()

    def fake_load_state(path):
        calls.append(("load", path))
        return loaded_state

    def fake_resume_run(state, resolved_answers, *, resolved_by, budget_usd):
        calls.append(("resume", state, resolved_answers, resolved_by, budget_usd))
        return _fake_state()

    monkeypatch.setattr("loop_orchestrator.slack_control.dispatch.load_state", fake_load_state)
    monkeypatch.setattr("loop_orchestrator.runner.resume_run", fake_resume_run)
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message", lambda **_: None
    )
    dispatcher = SlackRunDispatcher(bot_token="xoxb-fake")  # noqa: S106

    async def main() -> None:
        await dispatcher.dispatch_resume(
            **_resume_kwargs(snapshot_path=Path("state/run-1/02_awaiting_slack.json"))
        )
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == [
        ("load", Path("state/run-1/02_awaiting_slack.json")),
        ("resume", loaded_state, {1: "yes"}, "human:slack:1700000000.000100", 5.00),
    ]


def test_dispatch_resume_returns_before_the_resume_finishes(monkeypatch) -> None:
    started = threading.Event()
    release = threading.Event()

    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )

    def fake_resume_run(state, resolved_answers, *, resolved_by, budget_usd):
        started.set()
        assert release.wait(timeout=5), "test deadlocked waiting for release"
        return _fake_state()

    monkeypatch.setattr("loop_orchestrator.runner.resume_run", fake_resume_run)
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message", lambda **_: None
    )
    dispatcher = SlackRunDispatcher()

    async def main() -> float:
        t0 = time.monotonic()
        await dispatcher.dispatch_resume(**_resume_kwargs())
        elapsed = time.monotonic() - t0
        release.set()
        await asyncio.sleep(0.2)
        return elapsed

    elapsed = asyncio.run(main())

    assert elapsed < 1.0


def test_second_dispatch_resume_for_same_envelope_while_active_is_a_no_op(monkeypatch) -> None:
    entered = threading.Event()
    release = threading.Event()
    calls = []

    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )

    def fake_resume_run(state, resolved_answers, *, resolved_by, budget_usd):
        calls.append(resolved_by)
        entered.set()
        assert release.wait(timeout=5), "test deadlocked waiting for release"
        return _fake_state()

    monkeypatch.setattr("loop_orchestrator.runner.resume_run", fake_resume_run)
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message", lambda **_: None
    )
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch_resume(**_resume_kwargs(envelope_id="env-dup"))
        await asyncio.to_thread(entered.wait, 5)
        await dispatcher.dispatch_resume(**_resume_kwargs(envelope_id="env-dup"))
        await asyncio.sleep(0.1)
        release.set()
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert len(calls) == 1


def test_second_dispatch_resume_for_same_thread_but_distinct_envelope_is_a_no_op(
    monkeypatch,
) -> None:
    """Architect/security-critic finding on this PR: the paused snapshot
    stays `awaiting_slack` on disk until the resume actually finishes, so
    two *distinct* human replies to the same thread (different
    envelope_ids -- envelope_id dedupe alone would let both through) must
    still not both dispatch a resume."""
    entered = threading.Event()
    release = threading.Event()
    calls = []

    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )

    def fake_resume_run(state, resolved_answers, *, resolved_by, budget_usd):
        calls.append(resolved_by)
        entered.set()
        assert release.wait(timeout=5), "test deadlocked waiting for release"
        return _fake_state()

    monkeypatch.setattr("loop_orchestrator.runner.resume_run", fake_resume_run)
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message", lambda **_: None
    )
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch_resume(
            **_resume_kwargs(envelope_id="env-first-reply", thread_ts="1700000000.000100")
        )
        await asyncio.to_thread(entered.wait, 5)
        # A distinct envelope_id, same thread -- must still be a no-op while
        # the first resume for this thread is in flight.
        await dispatcher.dispatch_resume(
            **_resume_kwargs(envelope_id="env-second-reply", thread_ts="1700000000.000100")
        )
        await asyncio.sleep(0.1)
        release.set()
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert len(calls) == 1


def test_dispatch_resume_is_dispatchable_again_for_the_same_thread_after_it_finishes(
    monkeypatch,
) -> None:
    calls = []

    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )
    monkeypatch.setattr(
        "loop_orchestrator.runner.resume_run",
        lambda state, resolved_answers, *, resolved_by, budget_usd: (
            calls.append(resolved_by) or _fake_state()
        ),
    )
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message", lambda **_: None
    )
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch_resume(
            **_resume_kwargs(envelope_id="env-a", thread_ts="1700000000.000100")
        )
        await asyncio.sleep(0.2)
        # A second, later reply to the same thread AFTER the first resume
        # finished (e.g. a re-pause on a new thread wouldn't reuse this
        # thread_ts in practice, but the dedupe set itself must still
        # release) is not permanently blocked.
        await dispatcher.dispatch_resume(
            **_resume_kwargs(envelope_id="env-b", thread_ts="1700000000.000100")
        )
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert len(calls) == 2
    assert dispatcher._active_threads == set()


def test_dispatch_and_dispatch_resume_serialize_under_the_same_lock(monkeypatch) -> None:
    """A start (`dispatch`) and a resume (`dispatch_resume`) must not race
    the process-global `os.chdir` (BL-8) -- both must be serialized by the
    same `_run_lock`."""
    order = []
    release_run_new = threading.Event()

    def fake_run_new(human_input, *, budget_usd, loop_name):
        order.append("start:run_new")
        assert release_run_new.wait(timeout=5), "test deadlocked waiting for release"
        order.append("end:run_new")
        return MagicMock()

    def fake_resume_run(state, resolved_answers, *, resolved_by, budget_usd):
        order.append("start:resume_run")
        order.append("end:resume_run")
        return _fake_state()

    monkeypatch.setattr("loop_orchestrator.runner.run_new", fake_run_new)
    monkeypatch.setattr("loop_orchestrator.runner.resume_run", fake_resume_run)
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message", lambda **_: None
    )
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_command(envelope_id="env-start"))
        await dispatcher.dispatch_resume(**_resume_kwargs(envelope_id="env-resume"))
        await asyncio.sleep(0.1)
        # The resume must not have started yet -- the lock is held by the start.
        assert order == ["start:run_new"]
        release_run_new.set()
        await asyncio.sleep(0.2)
        assert order == ["start:run_new", "end:run_new", "start:resume_run", "end:resume_run"]

    asyncio.run(main())


def test_dispatch_resume_failure_is_logged_and_releases_the_dedupe_key(monkeypatch, caplog) -> None:
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )

    def failing_resume_run(state, resolved_answers, *, resolved_by, budget_usd):
        raise RuntimeError("boom")

    calls = []
    monkeypatch.setattr("loop_orchestrator.runner.resume_run", failing_resume_run)
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message",
        lambda **kwargs: calls.append(kwargs),
    )
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        with caplog.at_level("ERROR", logger="loop_orchestrator.slack_control.dispatch"):
            await dispatcher.dispatch_resume(**_resume_kwargs(envelope_id="env-resume-fail"))
            await asyncio.sleep(0.2)
            # The dedupe key was released, so a second attempt is not a no-op.
            await dispatcher.dispatch_resume(**_resume_kwargs(envelope_id="env-resume-fail"))
            await asyncio.sleep(0.2)

    asyncio.run(main())

    assert "resume failed for envelope env-resume-fail" in caplog.text
    # A failed resume never reaches the outcome post.
    assert calls == []


def test_dispatch_resume_posts_the_mapped_outcome_for_each_terminal_status(monkeypatch) -> None:
    posted = []

    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message",
        lambda **kwargs: posted.append(kwargs),
    )
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )

    async def _run_for_status(status: str, dispatcher: SlackRunDispatcher) -> None:
        await dispatcher.dispatch_resume(**_resume_kwargs(envelope_id=f"env-{status}"))
        await asyncio.sleep(0.2)

    for status in ("completed", "failed_stage", "budget_exceeded", "awaiting_slack"):
        posted.clear()
        monkeypatch.setattr(
            "loop_orchestrator.runner.resume_run",
            lambda state, resolved_answers, *, resolved_by, budget_usd, _status=status: _fake_state(
                _status
            ),
        )
        dispatcher = SlackRunDispatcher(bot_token="xoxb-fake")  # noqa: S106

        asyncio.run(_run_for_status(status, dispatcher))

        assert len(posted) == 1
        assert posted[0]["channel_id"] == "C1"
        assert posted[0]["thread_ts"] == "1700000000.000100"
        if status == "awaiting_slack":
            assert "new thread" in posted[0]["text"].lower()
        else:
            assert posted[0]["text"]


def test_dispatch_resume_skips_the_outcome_post_when_no_bot_token_configured(monkeypatch) -> None:
    posted = []
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.send_thread_message",
        lambda **kwargs: posted.append(kwargs),
    )
    monkeypatch.setattr(
        "loop_orchestrator.slack_control.dispatch.load_state", lambda path: _fake_state()
    )
    monkeypatch.setattr(
        "loop_orchestrator.runner.resume_run",
        lambda state, resolved_answers, *, resolved_by, budget_usd: _fake_state(),
    )
    dispatcher = SlackRunDispatcher()  # no bot_token

    async def main() -> None:
        await dispatcher.dispatch_resume(**_resume_kwargs())
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert posted == []
