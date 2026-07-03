### FILEPATH: /sprints/07_default_loop_and_cli/sprint_plan.md

**Sprint Goal:** Compose the four default personas into the ordered default loop and expose it via a Typer CLI entrypoint and the library's public API.

**Dependencies:** Sprint 05 (sequential_execution_engine), Sprint 06 (default_persona_implementations)

**Security Considerations:** The CLI is a thin wrapper with no independent credential or file-write logic. It must not import `keyring` and must not accept the API key as a command-line argument or option at any point. This sprint extends the sole-keyring-importer AST scan to include the CLI module.

**Risks & Blockers:** None identified.

**Tasks:**

- **Task 1: Default Loop Definition**
  - **Description:** Implement `DEFAULT_LOOP: list[BasePersona]` in `src/loop_engine/loops/default/loop.py` as `[PMPersona(), ArchitecturePersona(), AgileSprintBreakdownPersona(), CoderIacPersona()]`. No YAML/JSON/declarative loop-definition format is introduced.
  - **Target Files:** `src/loop_engine/loops/default/loop.py`, `src/loop_engine/loops/default/__init__.py`
  - **Acceptance Criteria:** `tests/loops/test_default.py` verifies `DEFAULT_LOOP` is a `list` of length 4, each element an instance of `BasePersona`, in the order PM, Architecture, Agile Sprint Breakdown, Coder/IaC.

- **Task 2: Public Library API**
  - **Description:** Export `run_loop`, `State`, `DEFAULT_LOOP`, and `LLMClient` from `src/loop_engine/__init__.py` so that `import loop_engine` exposes the full programmatic surface without requiring the CLI.
  - **Target Files:** `src/loop_engine/__init__.py`
  - **Acceptance Criteria:** `tests/test_public_api.py` verifies each of the four names is importable directly from the top-level `loop_engine` package.

- **Task 3: Typer CLI Entrypoint**
  - **Description:** Implement `src/loop_engine/cli.py` with a Typer app exposing `loop-engine run --loop <name> --input <path> [--budget <int>] [--resume-from <path>]`, resolving `<name>` to `DEFAULT_LOOP` when `"default"` is passed, reading `--input` as the seed content for the initial `State`, constructing an `LLMClient` with `--budget` (default `100000` tokens), and invoking `run_loop`.
  - **Target Files:** `src/loop_engine/cli.py`, `pyproject.toml` (adding `[project.scripts]` entry `loop-engine = "loop_engine.cli:app"`)
  - **Acceptance Criteria:** `hatch run loop-engine --help` exits zero and lists the `run` subcommand with `--loop`, `--input`, `--budget`, and `--resume-from` options.

- **Task 4: Resume-From-State Support**
  - **Description:** Implement `--resume-from <path>` in `cli.py`, loading a prior `State` snapshot via `State.model_validate_json()` from the given path and using it as the loop's starting state instead of constructing a fresh one from `--input`.
  - **Target Files:** `src/loop_engine/cli.py`
  - **Acceptance Criteria:** `tests/test_cli.py` verifies invoking the CLI with `--resume-from` pointing at a fixture state file skips PM-stage re-execution, asserted by the loop starting at the persona index implied by the fixture's `stage_history` length.

- **Task 5 (Security): CLI Keyring Boundary Extension**
  - **Description:** Extend the existing AST-based sole-keyring-importer test to include `src/loop_engine/cli.py` in its scanned file set, and add an explicit assertion that no `--api-key` or equivalent CLI option is defined on the Typer app.
  - **Target Files:** `tests/tools/test_keyring_boundary.py`, `tests/test_cli.py`
  - **Acceptance Criteria:** Both tests pass against the current `cli.py`.

---
