import asyncio
import threading
import time
from unittest.mock import MagicMock

from loop_engine.slack_control.command import SlackRunCommand
from loop_engine.slack_control.dispatch import SlackRunDispatcher


def _command(
    envelope_id: str = "env-1", human_input: str = "do it", channel_id: str = "C1"
) -> SlackRunCommand:
    return SlackRunCommand(
        human_input=human_input, budget_usd=5.00, channel_id=channel_id, envelope_id=envelope_id
    )


def test_dispatch_invokes_runner_once_with_command_fields(monkeypatch) -> None:
    calls = []

    def fake_run_new(human_input, *, budget_usd, loop_name):
        calls.append((human_input, budget_usd, loop_name))
        return MagicMock()

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
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

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
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

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
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

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
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

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
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

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
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

    monkeypatch.setattr("loop_engine.runner.run_new", failing_run_new)
    dispatcher = SlackRunDispatcher()

    async def main() -> None:
        with caplog.at_level("ERROR", logger="loop_engine.slack_control.dispatch"):
            await dispatcher.dispatch(_command(envelope_id="env-7"))
            await asyncio.sleep(0.2)
            await dispatcher.dispatch(_command(envelope_id="env-7"))
            await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == ["do it", "do it"]
    assert "run failed for envelope env-7" in caplog.text
