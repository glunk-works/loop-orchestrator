import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from loop_engine.tools.state_io.writer import (
    AGENT_MEMORY_PATH,
    AGENT_SCRATCHPAD_PATH,
    append_agent_memory,
    write_agent_scratchpad,
)

# Stable section anchors so parsing is deterministic (never LLM-interpreted).
_SCRATCHPAD_HEADER = "# Agent Scratchpad"
_ACTIVE_TASK_ANCHOR = "## Active Task"
_BLOCKED_ITEMS_ANCHOR = "## Blocked Items"
_COMPLETED_TASKS_ANCHOR = "## Completed Tasks"
_NONE_MARKER = "_none_"

_MEMORY_HEADER = (
    "# Decision & Lessons Ledger\n\n"
    "<!-- Append-only. Finalized architectural decisions and lessons learned. "
    "Never edit or remove existing entries. -->\n"
)
_ENTRY_SEPARATOR = "\n---\n"


class ScratchpadState(BaseModel):
    """The mutable `.agent/STATE.md` working state."""

    model_config = ConfigDict(extra="forbid")

    active_task: str | None = None
    blocked_items: list[str] = Field(default_factory=list)
    # The Ralph loop's task checklist: ids of manifest tasks already completed.
    # The authoritative "what's done" progress record across iterations.
    completed_tasks: list[str] = Field(default_factory=list)


class MemoryEntry(BaseModel):
    """One finalized entry in the append-only `.agent/MEMORY.md` ledger."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    recorded_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


def _render_scratchpad(state: ScratchpadState) -> str:
    active = (
        state.active_task.strip()
        if state.active_task and state.active_task.strip()
        else _NONE_MARKER
    )
    if state.blocked_items:
        blocked = "\n".join(f"- {item}" for item in state.blocked_items)
    else:
        blocked = _NONE_MARKER
    if state.completed_tasks:
        completed = "\n".join(f"- {item}" for item in state.completed_tasks)
    else:
        completed = _NONE_MARKER
    return (
        f"{_SCRATCHPAD_HEADER}\n\n"
        "<!-- Mutable working state for the active run. Overwritten each update. -->\n\n"
        f"{_ACTIVE_TASK_ANCHOR}\n\n{active}\n\n"
        f"{_BLOCKED_ITEMS_ANCHOR}\n\n{blocked}\n\n"
        f"{_COMPLETED_TASKS_ANCHOR}\n\n{completed}\n"
    )


def _section_body(text: str, anchor: str) -> str:
    # Content from `anchor` up to the next top-level `## ` header or EOF.
    pattern = re.compile(rf"^{re.escape(anchor)}\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _parse_scratchpad(text: str) -> ScratchpadState:
    active_raw = _section_body(text, _ACTIVE_TASK_ANCHOR)
    active = None if active_raw in ("", _NONE_MARKER) else active_raw

    blocked = _parse_bullets(_section_body(text, _BLOCKED_ITEMS_ANCHOR))
    completed = _parse_bullets(_section_body(text, _COMPLETED_TASKS_ANCHOR))
    return ScratchpadState(active_task=active, blocked_items=blocked, completed_tasks=completed)


def _parse_bullets(raw: str) -> list[str]:
    items: list[str] = []
    if raw and raw != _NONE_MARKER:
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())
    return items


def read_scratchpad() -> ScratchpadState:
    """Read `.agent/STATE.md`, or an empty scratchpad if it does not exist."""
    path = Path(*AGENT_SCRATCHPAD_PATH.split("/"))
    if not path.exists():
        return ScratchpadState()
    return _parse_scratchpad(path.read_text(encoding="utf-8"))


def write_scratchpad(state: ScratchpadState) -> Path:
    """Overwrite `.agent/STATE.md` with the rendered scratchpad."""
    return write_agent_scratchpad(_render_scratchpad(state))


def _render_entry(entry: MemoryEntry) -> str:
    return (
        f"\n## {entry.title}\n\n_recorded {entry.recorded_at}_\n\n{entry.body}\n{_ENTRY_SEPARATOR}"
    )


def read_memory() -> list[MemoryEntry]:
    """Parse the `.agent/MEMORY.md` ledger into its entries (oldest first)."""
    path = Path(*AGENT_MEMORY_PATH.split("/"))
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    entries: list[MemoryEntry] = []
    # Each entry is `## <title>` then `_recorded <ts>_` then the body.
    pattern = re.compile(
        r"^## (?P<title>.+?)\s*$\s*_recorded (?P<ts>.+?)_\s*(?P<body>.*?)(?=^---\s*$|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        body = match.group("body").strip()
        if not body:
            continue
        entries.append(
            MemoryEntry(
                title=match.group("title").strip(),
                body=body,
                recorded_at=match.group("ts").strip(),
            )
        )
    return entries


def append_memory(entry: MemoryEntry) -> Path:
    """Append one entry to `.agent/MEMORY.md` (creating the header on first write).

    The state_io writer enforces the append-only invariant: this can only ever
    extend the ledger, never rewrite it.
    """
    path = Path(*AGENT_MEMORY_PATH.split("/"))
    existing = path.read_text(encoding="utf-8") if path.exists() else _MEMORY_HEADER
    return append_agent_memory(existing + _render_entry(entry))
