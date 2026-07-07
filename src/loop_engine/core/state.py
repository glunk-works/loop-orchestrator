from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CURRENT_SCHEMA_VERSION = 2


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED_STAGE = "failed_stage"
    BUDGET_EXCEEDED = "budget_exceeded"
    AWAITING_ISSUE = "awaiting_issue"


class StageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage_name: str
    tokens_used: int = Field(ge=0)
    cost_usd: float
    completed_at: str
    # Prompt-cache activity for the stage; defaulted so pre-caching snapshots
    # still validate without a schema_version bump.
    cache_creation_input_tokens: int = Field(default=0, ge=0)
    cache_read_input_tokens: int = Field(default=0, ge=0)


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    origin_stage: str
    text: str
    resolution: str | None = None
    # "architect" | "pm" | "human:<issue-number>" — recorded, not enum-constrained,
    # so custom loops can add resolver layers without a schema change.
    resolved_by: str | None = None
    impact: Literal["task", "plan", "architecture"] | None = None
    # Finer-grained attribution within the origin stage (e.g. the sprint plan
    # path that raised the question), so re-entry can rework only the affected
    # unit instead of the whole stage. Defaulted: no schema_version bump.
    origin_detail: str | None = None


class IssueRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    url: str


class State(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    run_id: str
    status: RunStatus = RunStatus.RUNNING
    questions: list[Question] = Field(default_factory=list)
    pending_issue: IssueRef | None = None
    # Escalation/re-plan counters keyed by edge name (e.g. "escalations:CoderIacPersona",
    # "replans"); the engine enforces hard caps against these so feedback edges
    # cannot cycle unboundedly.
    counters: dict[str, int] = Field(default_factory=dict)
    stage_history: list[StageRecord]
    artifacts: dict[str, str]


def migrate_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a persisted snapshot payload to CURRENT_SCHEMA_VERSION.

    schema_version 1 predates status/questions/pending_issue/counters; every
    v2 addition has a default, so migration is just a version bump. Raises
    ValueError for versions this build doesn't know how to read.
    """
    version = payload.get("schema_version")
    if version == CURRENT_SCHEMA_VERSION:
        return payload
    if version == 1:
        return {**payload, "schema_version": CURRENT_SCHEMA_VERSION}
    raise ValueError(f"Unsupported State schema_version: {version!r}")
