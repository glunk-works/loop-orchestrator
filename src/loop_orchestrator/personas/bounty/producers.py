"""The injected-collaborator seam for the bounty loop's stub personas
(P1-D3). `ArtifactProducer` is the stable contract S47/S48 mount the real
recon/mapping data paths behind, swapping only the producer passed to
`ReconPersona`/`SurfaceMapPersona` — the persona shells, the loop wiring, and
the gates never change.
"""

import json
from typing import Protocol

from loop_orchestrator.core.state import BountyRunState


class ArtifactProducer(Protocol):
    """Returns an artifact body (a `str`, matching `State.artifacts`'s value
    type) for the given bounty run's namespaced state. Never receives
    `state`, `llm_client`, or `findings` — the persona shell owns those."""

    def __call__(self, bounty: BountyRunState) -> str: ...


def fixture_asset_inventory(bounty: BountyRunState) -> str:
    """Default Recon-stage stub: a valid, deterministic JSON list so the
    `asset_inventory` gate (`parse_json="list"`) ACCEPTs on the first
    attempt. Real inventory rows land in S47 behind this same seam."""
    return json.dumps([])


def fixture_surface_map(bounty: BountyRunState) -> str:
    """Default Surface-Mapping-stage stub: a valid, deterministic JSON
    object so the `surface_map` gate (`parse_json="object"`) ACCEPTs on the
    first attempt. The real mapping body lands in S48 behind this same
    seam."""
    return json.dumps({})
