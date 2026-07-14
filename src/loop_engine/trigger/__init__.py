"""The trigger surface: a GitHub webhook that dispatches a loop-engine run.

An orchestrator-level caller (sibling to `cli.py`), not a `tools/` module and
not an MCP server. Imports no `keyring`, writes no files directly, and adds
no subprocess surface — see `tests/trigger/test_boundaries.py`.
"""

from loop_engine.trigger.dispatch import InProcessDispatcher, RunDispatcher
from loop_engine.trigger.parse import RunRequest, parse_event

__all__ = ["InProcessDispatcher", "RunDispatcher", "RunRequest", "parse_event"]
