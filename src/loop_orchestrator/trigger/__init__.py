"""The trigger surface: a GitHub webhook that dispatches a loop-orchestrator run.

An orchestrator-level caller (sibling to `cli.py`), not a `tools/` module and
not an MCP server. Imports no `keyring`, writes no files directly, and adds
no subprocess surface — see `tests/trigger/test_boundaries.py`.
"""

from loop_orchestrator.trigger.dispatch import InProcessDispatcher, RunDispatcher
from loop_orchestrator.trigger.parse import RunRequest, parse_event

__all__ = ["InProcessDispatcher", "RunDispatcher", "RunRequest", "parse_event"]
