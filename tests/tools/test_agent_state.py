from pathlib import Path

import pytest
from pydantic import ValidationError

from loop_orchestrator.tools.agent_state import (
    MemoryEntry,
    ScratchpadState,
    append_memory,
    read_memory,
    read_scratchpad,
    write_scratchpad,
)
from loop_orchestrator.tools.state_io.writer import (
    AGENT_MEMORY_PATH,
    AppendOnlyViolationError,
    append_agent_memory,
    write_agent_scratchpad,
)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_scratchpad_round_trips() -> None:
    state = ScratchpadState(
        active_task="Wire the LangGraph node", blocked_items=["awaiting issue #4"]
    )
    path = write_scratchpad(state)

    assert path == Path(".agent") / "STATE.md"
    assert read_scratchpad() == state


def test_empty_scratchpad_round_trips_as_none() -> None:
    write_scratchpad(ScratchpadState())
    reloaded = read_scratchpad()

    assert reloaded.active_task is None
    assert reloaded.blocked_items == []


def test_read_scratchpad_absent_returns_empty() -> None:
    assert read_scratchpad() == ScratchpadState()


def test_memory_is_append_only_and_ordered() -> None:
    append_memory(MemoryEntry(title="Adopt LangGraph", body="Rebuild run_loop on a StateGraph."))
    append_memory(MemoryEntry(title="Externalize state", body="Move artifacts to disk."))

    entries = read_memory()
    assert [e.title for e in entries] == ["Adopt LangGraph", "Externalize state"]
    assert entries[1].body == "Move artifacts to disk."

    # The first entry's text is still present verbatim after the second append.
    assert "Rebuild run_loop on a StateGraph." in Path(*AGENT_MEMORY_PATH.split("/")).read_text()


def test_append_agent_memory_rejects_non_prefix_rewrite() -> None:
    append_agent_memory("# Ledger\n\n## First\nbody\n")
    with pytest.raises(AppendOnlyViolationError):
        append_agent_memory("# Ledger\n\n## Rewritten\n")


def test_memory_entry_rejects_blank_fields() -> None:
    with pytest.raises(ValidationError):
        MemoryEntry(title="", body="x")
    with pytest.raises(ValidationError):
        MemoryEntry(title="x", body="")


def test_scratchpad_state_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ScratchpadState(active_task="x", bogus="y")


def test_write_agent_scratchpad_rejects_traversal() -> None:
    # The public API only ever passes constants, but the writer guards anyway.
    from loop_orchestrator.tools.state_io import writer

    with pytest.raises(ValueError):
        writer._agent_target("../escape.md")
    assert write_agent_scratchpad("content") == Path(".agent") / "STATE.md"
