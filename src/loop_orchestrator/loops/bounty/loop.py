from loop_orchestrator.core.engine import Loop, Stage
from loop_orchestrator.core.gates import ArtifactGate
from loop_orchestrator.personas.bounty.recon import ReconPersona
from loop_orchestrator.personas.bounty.surface_map import SurfaceMapPersona


def build_bounty_loop() -> Loop:
    """The Phase-1 bounty loop: Recon/Inventory → Surface-Mapping.

    The walking skeleton (P1-D3): both stages are wired now, behind stub
    personas emitting fixture artifacts, so the full loop runs green
    end-to-end hermetically. S47 replaces the Recon persona's injected
    producer with the real dispatch→S3→IDP data path; S48 replaces
    Mapping's. The loop wiring and the gates do not churn again.

    `impact_reentry` below is planted ahead of core support, not exercised
    from day one: `Question.impact` (`core/state.py`) has no `"scope"` or
    `"surface"` member, `reentry_index()` (`core/engine.py`) only ever
    checks `("architecture", "plan")`, and `VALID_IMPACTS`
    (`personas/resolution.py`) filters both out — so a `"scope"` or
    `"surface"` resolution can never reach this map today. Making it live is
    three core edits, deferred to S47/S48 by P1-D3 to avoid churning
    `core/` in this skeleton PR. The resolvers/escalation path for this loop
    is likewise not yet live.

    Rebuilt per run (mirroring `build_default_loop()`'s posture) rather than
    reused from `BOUNTY_LOOP`.
    """
    recon = ReconPersona()

    return Loop(
        stages=[
            Stage(
                persona=recon,
                gate=ArtifactGate("asset_inventory", parse_json="list"),
            ),
            Stage(
                persona=SurfaceMapPersona(),
                gate=ArtifactGate("surface_map", parse_json="object"),
                resolvers=[recon],
            ),
        ],
        # Forward-declared blast-radius targets for when scope/surface impact
        # re-entry lands (S47/S48): "scope" -> Recon (index 0), "surface" ->
        # Surface-Mapping (index 1). Inert until then -- see the docstring above.
        impact_reentry={"scope": 0, "surface": 1},
    )


BOUNTY_LOOP = build_bounty_loop()
