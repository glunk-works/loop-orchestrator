from loop_orchestrator.core.state import State
from loop_orchestrator.personas.base import BasePersona
from loop_orchestrator.personas.bounty.producers import ArtifactProducer, fixture_asset_inventory


class ReconPersona(BasePersona):
    """Stage 0: Recon/Inventory. Owns the fail-closed `state.bounty is None`
    guard (a bounty run with no rules-of-engagement target is a
    misconfiguration, not a silent no-op — `target_id` is not an artifact,
    so this raise is its only guard; the engine's `consumes` pre-check
    never covers it) and delegates the artifact body to the injected
    `ArtifactProducer`. S47 swaps `producer` for the real
    dispatch→S3→IDP data path; this shell does not change (P1-D3)."""

    produces = ("asset_inventory",)

    def __init__(self, producer: ArtifactProducer = fixture_asset_inventory) -> None:
        self._producer = producer

    def run(self, state: State, llm_client, findings: list[str] | None = None) -> State:
        if state.bounty is None:
            raise ValueError(
                "ReconPersona requires state.bounty to be set (a bounty run needs a target_id)"
            )
        body = self._producer(state.bounty)
        return state.model_copy(update={"artifacts": {**state.artifacts, "asset_inventory": body}})
