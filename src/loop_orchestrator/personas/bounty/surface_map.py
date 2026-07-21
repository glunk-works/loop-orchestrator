from loop_orchestrator.core.state import State
from loop_orchestrator.personas.base import BasePersona
from loop_orchestrator.personas.bounty.producers import ArtifactProducer, fixture_surface_map


class SurfaceMapPersona(BasePersona):
    """Stage 1: Surface-Mapping. Consumes the Recon stage's `asset_inventory`
    (the engine's `consumes` pre-check guarantees it is already set, and by
    then `state.bounty` is guaranteed non-`None` — `ReconPersona` raised
    otherwise) and delegates the artifact body to the injected
    `ArtifactProducer`. S48 swaps `producer` for the real mapping data path;
    this shell does not change (P1-D3)."""

    consumes = ("asset_inventory",)
    produces = ("surface_map",)

    def __init__(self, producer: ArtifactProducer = fixture_surface_map) -> None:
        self._producer = producer

    def run(self, state: State, llm_client, findings: list[str] | None = None) -> State:
        body = self._producer(state.bounty)
        return state.model_copy(update={"artifacts": {**state.artifacts, "surface_map": body}})
