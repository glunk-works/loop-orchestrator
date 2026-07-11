"""Declarative persona layer (Phase 4 · part 2).

`GeneratorNode` — one config-driven single-shot node — replaces the per-class
boilerplate of the Architecture, Sprint Breakdown, and PM personas. Phase 6
deleted those three persona classes and the `LOOP_ENGINE_PERSONAS` flag that
selected between them: these nodes are now the only document personas, and
`prompts/` is the sole source of truth for their prompt content.
See `docs/migration_roadmap.md` (Phase 4, Phase 6).
"""
