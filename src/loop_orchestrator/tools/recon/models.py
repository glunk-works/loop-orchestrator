"""The recon input boundary's carrier (S47-D3, P1-D6 input half).
`ReconRequest` pairs the seed a caller wants scanned with the S47-D8
correlation token that links the async `gh workflow_dispatch` run back to
its deterministic S3 output key (`recon/<token>.jsonl`). Every function in
this module takes its `rules: ScopeRules` as a parameter (B5) -- `tools/recon`
never loads a target itself.
"""

from pydantic import BaseModel, ConfigDict
from scope_core import ScopeRules, validate_target


class ReconRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: str
    correlation_token: str


def build_recon_request(rules: ScopeRules, seed: str, correlation_token: str) -> ReconRequest:
    """The input half of P1-D6's scope boundary: `validate_target` raises
    `ScopeViolation` before any `ReconRequest` is constructed, so an
    out-of-scope seed never reaches `ReconDispatcher.dispatch` -- let alone
    a live `gh workflow_dispatch` call."""
    validate_target(rules, seed)
    return ReconRequest(seed=seed, correlation_token=correlation_token)
