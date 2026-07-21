from loop_orchestrator.core.engine import Loop, Stage
from loop_orchestrator.core.gates import ArtifactGate
from loop_orchestrator.personas.bounty.recon import ReconPersona
from loop_orchestrator.personas.bounty.surface_map import SurfaceMapPersona


def build_bounty_loop() -> Loop:
    """The Phase-1 bounty loop: Recon/Inventory → Surface-Mapping.

    The walking skeleton (P1-D3): both stages are wired now, behind stub
    personas emitting fixture artifacts, so the full loop runs green
    end-to-end hermetically and `impact_reentry` is exercised from day one.
    S47 replaces the Recon persona's injected producer with the real
    dispatch→S3→IDP data path; S48 replaces Mapping's. The loop wiring, the
    gates, and the re-entry map do not churn again.

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
        # Blast-radius re-entry: a "scope" question re-enters Recon (index 0);
        # a "surface" question re-enters Surface-Mapping (index 1).
        impact_reentry={"scope": 0, "surface": 1},
    )


BOUNTY_LOOP = build_bounty_loop()
