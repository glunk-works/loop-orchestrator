### FILEPATH: /sprints/04_state_persistence_and_artifacts/sprint_plan.md

**Sprint Goal:** Implement the sole modules permitted to write `State` snapshots and produced artifacts to disk.

**Dependencies:** Sprint 02 (state_and_persona_contract)

**Security Considerations:** `tools/state_io` is the sole writer to `state/`, `docs/`, and `sprints/`. The threat surface is path traversal if a `run_id` or artifact name contains directory-escaping characters (for example `../`). Mitigation: validate `run_id` and artifact names against a strict allow-listed pattern before constructing any file path, and reject the operation before any filesystem call is made.

**Risks & Blockers:** None identified.

**Tasks:**

- **Task 1: State Snapshot Writer**
  - **Description:** Implement `write_state_snapshot(state: State, run_id: str, stage_index: int, stage_name: str) -> pathlib.Path` in `src/loop_engine/tools/state_io/writer.py`, writing `state.model_dump_json()` to `state/<run_id>/<NN_stage_name>.json`, where `NN` is `stage_index` zero-padded to two digits.
  - **Target Files:** `src/loop_engine/tools/state_io/writer.py`
  - **Acceptance Criteria:** `tests/tools/test_state_io.py` verifies the written file's contents parse back into an equivalent `State` object via `State.model_validate_json()`.

- **Task 2 (Security): Path Traversal Rejection**
  - **Description:** Add input validation in `write_state_snapshot` and the artifact writer (Task 3), rejecting any `run_id` or artifact name that does not match `^[A-Za-z0-9_-]+$`, raising `ValueError` before any filesystem operation is attempted.
  - **Target Files:** `src/loop_engine/tools/state_io/writer.py`
  - **Acceptance Criteria:** `tests/tools/test_state_io.py` verifies `ValueError` is raised for a `run_id` value of `"../../etc"` and that no file is created on disk as a result.

- **Task 3: Artifact Writer**
  - **Description:** Implement `write_artifact(content: str, relative_path: str) -> pathlib.Path` in `src/loop_engine/tools/state_io/writer.py`, restricted to writing under `docs/`, `sprints/`, or `src/` — validate that the normalized `relative_path` starts with one of these three prefixes and raise `ValueError` otherwise.
  - **Target Files:** `src/loop_engine/tools/state_io/writer.py`
  - **Acceptance Criteria:** `tests/tools/test_state_io.py` verifies a write to `docs/example.md` succeeds and that a write to `/etc/passwd` or `../outside.md` raises `ValueError` with no file created.

- **Task 4: Sole-Writer Boundary Test**
  - **Description:** Write a static AST-based test in `tests/tools/test_state_io_boundary.py` scanning `src/loop_engine/` for any direct call to `open(`, `pathlib.Path.write_text`, or `pathlib.Path.write_bytes` outside `src/loop_engine/tools/state_io/`.
  - **Target Files:** `tests/tools/test_state_io_boundary.py`
  - **Acceptance Criteria:** The test passes against the current tree.

---
