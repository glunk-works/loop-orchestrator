# Decision & Lessons Ledger

<!-- Append-only. Finalized architectural decisions and lessons learned. Never edit or remove existing entries. -->

## Adopt LangGraph as the orchestration engine

_recorded 2026-07-08T00:52:21.344926+00:00_

run_loop is reimplemented as a StateGraph (core/graph_engine.py) behind LOOP_ENGINE_ENGINE=langgraph. The per-stage cycle is factored into execute_stage() so both engines are behaviorally identical; parity is test-guarded.

---

## Externalize artifacts via dual-field, strip in 1d

_recorded 2026-07-08T00:52:21.347128+00:00_

State gained artifact_refs (path+sha256 digest) alongside the inline artifacts body-dict (schema v3). tools/artifact_store.mirror_to_disk populates refs at snapshot time. Inline bodies are dropped once the LangGraph engine is the sole reader.

---
