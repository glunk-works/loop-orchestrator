"""Stub-persona behaviour for the S46 bounty loop skeleton: the fail-closed
missing-target raise, the default fixture producers, and the injected-producer
seam (P1-D3 — S47/S48 swap only this collaborator)."""

import json

import pytest

from loop_orchestrator.core.state import BountyRunState, State
from loop_orchestrator.personas.bounty.recon import ReconPersona
from loop_orchestrator.personas.bounty.surface_map import SurfaceMapPersona


def _state(**overrides) -> State:
    defaults = {"schema_version": 6, "run_id": "run-1", "stage_history": [], "artifacts": {}}
    return State(**{**defaults, **overrides})


def test_recon_persona_raises_when_bounty_is_none() -> None:
    persona = ReconPersona()
    with pytest.raises(ValueError, match="state.bounty"):
        persona.run(_state(bounty=None), llm_client=None)


def test_recon_persona_default_producer_emits_valid_json_list() -> None:
    persona = ReconPersona()
    state = _state(bounty=BountyRunState(target_id="target-001"))

    result = persona.run(state, llm_client=None)

    assert json.loads(result.artifacts["asset_inventory"]) == []
    # The stub is deterministic: re-running against the same bounty state
    # reproduces the identical body (a REVISE must not look like progress).
    assert (
        persona.run(state, llm_client=None).artifacts["asset_inventory"]
        == (result.artifacts["asset_inventory"])
    )


def test_recon_persona_uses_injected_producer() -> None:
    def custom_producer(bounty: BountyRunState) -> str:
        return json.dumps([bounty.target_id])

    persona = ReconPersona(producer=custom_producer)
    state = _state(bounty=BountyRunState(target_id="target-001"))

    result = persona.run(state, llm_client=None)

    assert json.loads(result.artifacts["asset_inventory"]) == ["target-001"]


def test_surface_map_persona_default_producer_emits_valid_json_object() -> None:
    persona = SurfaceMapPersona()
    state = _state(
        bounty=BountyRunState(target_id="target-001"),
        artifacts={"asset_inventory": "[]"},
    )

    result = persona.run(state, llm_client=None)

    assert json.loads(result.artifacts["surface_map"]) == {}


def test_surface_map_persona_uses_injected_producer() -> None:
    def custom_producer(bounty: BountyRunState) -> str:
        return json.dumps({"target": bounty.target_id})

    persona = SurfaceMapPersona(producer=custom_producer)
    state = _state(
        bounty=BountyRunState(target_id="target-001"),
        artifacts={"asset_inventory": "[]"},
    )

    result = persona.run(state, llm_client=None)

    assert json.loads(result.artifacts["surface_map"]) == {"target": "target-001"}
