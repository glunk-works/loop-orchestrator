import asyncio
import threading
import time
from unittest.mock import MagicMock

from loop_engine.trigger.dispatch import InProcessDispatcher
from loop_engine.trigger.parse import RunRequest


def _request(issue_number: int = 1, repo: str = "acme/widgets", human_input: str = "do it"):
    return RunRequest(human_input=human_input, repo_full_name=repo, issue_number=issue_number)


def test_dispatch_invokes_runner_once_with_request_fields(monkeypatch) -> None:
    calls = []

    def fake_run_new(human_input, *, budget_usd, loop_name):
        calls.append((human_input, budget_usd, loop_name))
        return MagicMock()

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
    dispatcher = InProcessDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_request(human_input="fix the bug"))
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
    dispatcher = InProcessDispatcher()

    async def main() -> float:
        t0 = time.monotonic()
        await dispatcher.dispatch(_request())
        elapsed = time.monotonic() - t0
        release.set()
        await asyncio.sleep(0.2)
        return elapsed

    elapsed = asyncio.run(main())

    assert elapsed < 1.0


def test_second_dispatch_for_same_issue_while_active_is_a_no_op(monkeypatch) -> None:
    entered = threading.Event()
    release = threading.Event()
    calls = []

    def fake_run_new(human_input, *, budget_usd, loop_name):
        calls.append(human_input)
        entered.set()
        assert release.wait(timeout=5), "test deadlocked waiting for release"
        return MagicMock()

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
    dispatcher = InProcessDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_request(issue_number=9))
        await asyncio.to_thread(entered.wait, 5)
        await dispatcher.dispatch(_request(issue_number=9))
        await asyncio.sleep(0.1)
        release.set()
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == ["do it"]


def test_issue_can_be_dispatched_again_after_run_completes(monkeypatch) -> None:
    calls = []

    def fake_run_new(human_input, *, budget_usd, loop_name):
        calls.append(human_input)
        return MagicMock()

    monkeypatch.setattr("loop_engine.runner.run_new", fake_run_new)
    dispatcher = InProcessDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_request(issue_number=3))
        await asyncio.sleep(0.2)
        await dispatcher.dispatch(_request(issue_number=3))
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
    dispatcher = InProcessDispatcher()

    async def main() -> None:
        await dispatcher.dispatch(_request(issue_number=11))
        await asyncio.to_thread(entered.wait, 5)
        assert len(dispatcher._tasks) == 1
        release.set()
        await asyncio.sleep(0.2)
        assert len(dispatcher._tasks) == 0

    asyncio.run(main())


def test_run_failure_is_logged_and_releases_the_dedupe_key(monkeypatch, caplog) -> None:
    calls = []

    def failing_run_new(human_input, *, budget_usd, loop_name):
        calls.append(human_input)
        raise RuntimeError("boom")

    monkeypatch.setattr("loop_engine.runner.run_new", failing_run_new)
    dispatcher = InProcessDispatcher()

    async def main() -> None:
        with caplog.at_level("ERROR", logger="loop_engine.trigger.dispatch"):
            await dispatcher.dispatch(_request(issue_number=7))
            await asyncio.sleep(0.2)
            await dispatcher.dispatch(_request(issue_number=7))
            await asyncio.sleep(0.2)

    asyncio.run(main())

    assert calls == ["do it", "do it"]
    assert "run failed for acme/widgets#7" in caplog.text
