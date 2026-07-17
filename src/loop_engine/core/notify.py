"""The notifier seam's pure contract: the seven lifecycle event kinds, the
event payload, and the `Notifier` protocol `run_graph_loop` emits through.

No `slack_sdk` import here (and none of `tools/slack_io`) — this module is a
leaf, mirroring how `core/engine` depends only on the `EscalationFiler` shape
and not on `tools/issue_io`'s/`tools/slack_io`'s concrete transports.
`tools/slack_io` imports the contract from here, never the reverse.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from loop_engine.core.state import State


class EventKind(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED_STAGE = "failed_stage"
    BUDGET_EXCEEDED = "budget_exceeded"
    AWAITING_ISSUE = "awaiting_issue"
    AWAITING_SLACK = "awaiting_slack"
    CRASHED = "crashed"


@dataclass(frozen=True)
class LifecycleEvent:
    kind: EventKind
    state: State
    budget_usd: float | None = None
    # Short exception type/message, set only for CRASHED — never a traceback
    # or a credential.
    error: str | None = None


class Notifier(Protocol):
    def emit(self, event: LifecycleEvent) -> None: ...


class NoOpNotifier:
    def emit(self, event: LifecycleEvent) -> None:
        pass
