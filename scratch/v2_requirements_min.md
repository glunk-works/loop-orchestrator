# textkit — Requirements Artifact (V2 minimal — COMPLETED-under-$5)

> Deliberately shrunk to **two** simple, independent functions so the run
> converges to terminal `COMPLETED` well under a $5 budget. Every field is a
> firm answer — no `OPEN`/`DRAFT` fields — so the PM/Architecture/Sprint
> Breakdown stages converge without human escalation. Still multi-task (two
> impl functions) so Ralph's one-task-per-iteration convergence is exercised.
>
> **src-only constraint (host-run staging):** the model-facing write allowlist
> is `(docs, sprints, src)` — the Coder cannot write repo-root files or a
> top-level `tests/`. ALL code AND tests live under `src/`, and the repo-root
> `pyproject.toml` (with `pythonpath`/`testpaths` at `src`) is pre-seeded, not
> written by the Coder.

## problem_statement

There is no small, well-tested collection of pure string helpers in this
workspace. We want a single self-contained Python package exposing two
independent, standard-library-only text utilities, each fully unit-tested.

## purpose_and_goals

Build **textkit**: a tiny pure-Python package under `src/textkit/` exposing two
independent, dependency-free functions, each an exact, closed specification with
its own tests. The functions are mutually independent (no shared state) so they
can be implemented one at a time and verified incrementally.

## target_users

The repo owner (Jared), as a self-contained reference/utility package. No
external users, no distribution requirements beyond a normal importable package.

## in_scope

- Package `src/textkit/__init__.py` re-exporting both functions.
- Module `src/textkit/slugify.py` — `slugify(s: str) -> str`.
- Module `src/textkit/word_count.py` — `word_count(s: str) -> int`.
- Colocated tests under `src/textkit/tests/` — one `test_<name>.py` per
  function, covering the known cases and the error cases below.

## out_of_scope / non_goals

- No CLI, no web interface, no file/network I/O, no logging.
- No third-party dependencies (standard library only).
- No repo-root files and no top-level `tests/` directory — everything the model
  writes lives under `src/` (the `pyproject.toml` is pre-seeded).
- Only the two functions above — no other utilities.

## functional_requirements

- Packaging (PRE-SEEDED, do not write): the target tree already ships a
  `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["src"]` and
  `testpaths = ["src"]`, so `pytest` from the repo root imports `textkit` and
  collects the colocated tests without an editable install. Do NOT create or
  edit `pyproject.toml`.
- `slugify(s)`: lowercase the string, strip leading/trailing whitespace,
  replace every run of non-alphanumeric characters with a single hyphen, and
  strip leading/trailing hyphens. Raises `TypeError` if `s` is not a `str`.
  **Known cases (input → output):**
  - `"  Hello, World!  "` → `"hello-world"`
  - `"foo_bar  baz"` → `"foo-bar-baz"`
  - `"--Already-Slugged--"` → `"already-slugged"`
  - `""` → `""`
  - `"!!!"` → `""`
- `word_count(s)`: return the number of whitespace-separated tokens — exactly
  `len(s.split())`, using Python's default `str.split()` semantics (any run of
  whitespace is a single separator; leading/trailing whitespace is ignored).
  Tokens are **not** further split on punctuation or hyphens — a hyphenated or
  punctuation-adjacent token counts as one token. The empty/whitespace-only
  string returns `0`. Raises `TypeError` if `s` is not a `str`.
  **Known cases (input → output):**
  - `"the quick brown fox"` → `4`
  - `"  spaced   out  words "` → `3`
  - `"well-known state-of-the-art"` → `2` (hyphenated words are one token each)
  - `"hello, world!"` → `2` (trailing punctuation stays attached to its token)
  - `""` → `0`; `"   "` → `0`

## integration_context

Standalone package. Layout: `src/textkit/` with colocated `src/textkit/tests/`.
Importable as `import textkit`. No external services, no network.

## acceptance_criteria

- `import textkit` exposes `slugify` and `word_count`.
- Each function meets its specification above, including every error case and
  every known case listed.
- The full pytest suite passes (`pytest -q` from the repo root, collecting
  `src/textkit/tests/`).
- `ruff check` and `ruff format --check` are clean.

## priority_ranking

- **must_have_v1:** both functions, their error handling, and their tests. All
  are required for v1.
- **later/nice-to-have:** none — the scope is intentionally closed.

## timeline_and_cost_estimates

Two small tasks (one per function); this is a reference utility, not a product.
No external deadline.

## risks_and_assumptions

- Assumption: Python 3.11+ standard library only; no third-party deps.
- Risk: none material — both functions are direct standard-library expressions.

## security_and_risk_considerations

Pure computation over in-memory strings. No secrets, no I/O, no network, no
credentials. Standard repo lint/format gates apply; nothing package-specific.

## regulatory_and_compliance_constraints

None.

## supply_chain_security_expectations

Standard-library only; no dependencies to audit. Normal ruff gates apply.

## cost_sensitivity

Low. This is a tiny utility; no runtime cost concerns.

## open_questions_for_architect

None — the scope, interfaces, and error semantics are fully specified above,
including explicit known-case input/output examples. Implement the two functions
and their colocated tests as stated, one at a time.
