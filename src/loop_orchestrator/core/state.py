from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CURRENT_SCHEMA_VERSION = 6


def default_artifact_path(run_id: str, key: str) -> str:
    """Where an artifact body is mirrored on disk. Stays under the `docs/`
    artifact root (see tools/state_io) and is unique per run + key."""
    return f"docs/artifacts/{run_id}/{key}"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED_STAGE = "failed_stage"
    BUDGET_EXCEEDED = "budget_exceeded"
    AWAITING_ISSUE = "awaiting_issue"
    AWAITING_SLACK = "awaiting_slack"


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


class SlackRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str
    message_ts: str


class BountyRunState(BaseModel):
    """Namespace for the bounty loop's own ID references (§4: `State` refers
    to inventory rows by ID, never embeds them). `extra="forbid"` only — NOT
    frozen: later stages add fields like `asset_ids`/`finding_ids` via
    `state.model_copy`, so this sub-model must stay mutable."""

    model_config = ConfigDict(extra="forbid")

    target_id: str


class State(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    run_id: str
    status: RunStatus = RunStatus.RUNNING
    questions: list[Question] = Field(default_factory=list)
    pending_issue: IssueRef | None = None
    pending_slack: SlackRef | None = None
    # Escalation/re-plan counters keyed by edge name (e.g. "escalations:RalphCoderPersona",
    # "replans"); the engine enforces hard caps against these so feedback edges
    # cannot cycle unboundedly.
    counters: dict[str, int] = Field(default_factory=dict)
    stage_history: list[StageRecord]
    # Inline artifact bodies — the single source of truth for artifact
    # content. Fed directly into the prompt-cache prefix (declarative/node.py),
    # so it is never externalized to disk on the read side; `artifact_store`
    # publishes it to `docs/artifacts/<run_id>/` as a side effect, not a
    # migration.
    artifacts: dict[str, str]
    # The bounty loop's own namespaced state; the default loop never sets
    # this. Additive with a None default — future bounty ID references go
    # inside BountyRunState, not as new top-level State fields.
    bounty: BountyRunState | None = None


_RETIRED_V3_KEY = "artifact_refs"


def migrate_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a persisted snapshot payload to CURRENT_SCHEMA_VERSION.

    v1 predates status/questions/pending_issue/counters; v2 predates a
    since-retired disk-ref field carried by v3 only; under `extra="forbid"`
    that field must be popped, not merely versioned past, or a v3 payload
    fails validation. v4 predates `pending_slack`, added purely additively
    (defaults to None) in v5. v5 predates `bounty`, added purely additively
    (defaults to None) in v6. Raises ValueError for versions this build
    can't read.
    """
    version = payload.get("schema_version")
    if version == CURRENT_SCHEMA_VERSION:
        return payload
    if version in (1, 2, 3, 4, 5):
        # An unconditional pop covers all five prior versions (v1/v2/v4/v5
        # never had the key) — the inline `artifacts` bodies carry forward
        # untouched.
        upgraded = {**payload, "schema_version": CURRENT_SCHEMA_VERSION}
        upgraded.pop(_RETIRED_V3_KEY, None)
        return upgraded
    raise ValueError(f"Unsupported State schema_version: {version!r}")
