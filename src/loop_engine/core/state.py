import hashlib
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CURRENT_SCHEMA_VERSION = 3


def artifact_digest(body: str) -> str:
    """Stable content digest for an artifact body (sha256 hex)."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


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


class ArtifactRef(BaseModel):
    """A pointer to an artifact body that lives on disk rather than inline in
    State. The routing state carries the path + digest, not the full text —
    the substrate the LangGraph state (Phase 1d) is stripped down to."""

    model_config = ConfigDict(extra="forbid")

    path: str
    digest: str
    size_bytes: int = Field(ge=0)


class State(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    run_id: str
    status: RunStatus = RunStatus.RUNNING
    questions: list[Question] = Field(default_factory=list)
    pending_issue: IssueRef | None = None
    # Escalation/re-plan counters keyed by edge name (e.g. "escalations:RalphCoderPersona",
    # "replans"); the engine enforces hard caps against these so feedback edges
    # cannot cycle unboundedly.
    counters: dict[str, int] = Field(default_factory=dict)
    stage_history: list[StageRecord]
    # Inline artifact bodies (schema v2 and earlier). Retained during the
    # migration so the pre-LangGraph run_loop and its tests keep working; the
    # bodies are ALSO mirrored to disk and pointed at by artifact_refs. The
    # inline bodies are dropped once the LangGraph engine (Phase 1d) is the
    # only reader.
    artifacts: dict[str, str]
    # Disk pointers (path + digest) for each artifact body. Defaulted so v2
    # snapshots validate unchanged; populated by tools/artifact_store.
    artifact_refs: dict[str, ArtifactRef] = Field(default_factory=dict)


def migrate_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a persisted snapshot payload to CURRENT_SCHEMA_VERSION.

    v1 predates status/questions/pending_issue/counters; v2 predates
    artifact_refs. Every field added since is defaulted, so migration is a
    version bump. Raises ValueError for versions this build can't read.
    """
    version = payload.get("schema_version")
    if version == CURRENT_SCHEMA_VERSION:
        return payload
    # v1 predates status/questions/pending_issue/counters; v2 predates
    # artifact_refs. Every field added since has a default, so upgrading is a
    # version bump — the inline `artifacts` bodies carry forward untouched and
    # are re-mirrored to disk (and pointed at by artifact_refs) on the next run.
    if version in (1, 2):
        return {**payload, "schema_version": CURRENT_SCHEMA_VERSION}
    raise ValueError(f"Unsupported State schema_version: {version!r}")
