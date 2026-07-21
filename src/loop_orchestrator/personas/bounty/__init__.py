"""Bounty loop personas — Phase 1 walking skeleton (P1-D3).

`ReconPersona`/`SurfaceMapPersona` are thin shells: each reads `State.bounty`,
delegates the artifact body to an injected `ArtifactProducer` collaborator
(`producers.py`), and writes the result. S47/S48 replace only the injected
producer with a real data path; the shells, the loop wiring, and the gates
do not change.
"""
