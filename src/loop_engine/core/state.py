from pydantic import BaseModel, ConfigDict, Field


class StageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage_name: str
    tokens_used: int = Field(ge=0)
    cost_usd: float
    completed_at: str


class State(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    run_id: str
    stage_history: list[StageRecord]
    artifacts: dict[str, str]
