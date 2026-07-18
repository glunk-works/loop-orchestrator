"""The `.agent/` semantic-state layer.

Two files hold the operational context that used to live inline in the
orchestrator's `State.artifacts` bag:

- `.agent/STATE.md` — a mutable scratchpad for the active task and blocked
  items (overwritten each update).
- `.agent/MEMORY.md` — an append-only ledger of finalized architectural
  decisions and lessons learned.

All writes are delegated to `tools/state_io` so the single-writer boundary
holds; this package only parses, renders, and reads.
"""

from loop_orchestrator.tools.agent_state.store import (
    MemoryEntry,
    ScratchpadState,
    append_memory,
    read_memory,
    read_scratchpad,
    write_scratchpad,
)

__all__ = [
    "MemoryEntry",
    "ScratchpadState",
    "append_memory",
    "read_memory",
    "read_scratchpad",
    "write_scratchpad",
]
