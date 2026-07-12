# textkit — Requirements Artifact (V2 Ralph convergence input)

> Small, fully-specified, **multi-task** spec for the Phase-6 V2 Ralph
> convergence + cost verification. Every field is a firm answer — no `OPEN`/
> `DRAFT` fields — so the PM stage converges on the happy path (no human
> escalation). Deliberately several small, independent functions so the Ralph
> Sprint Breakdown emits a multi-task manifest and the loop must converge one
> task per iteration.
>
> **src-only constraint (host-run staging):** the model-facing write allowlist
> is `(docs, sprints, src)` — the Coder cannot write repo-root files or a
> top-level `tests/`. Therefore ALL code AND tests live under `src/`, and the
> repo-root `pyproject.toml` (with `pythonpath`/`testpaths` pointing at `src`)
> is pre-seeded in the target tree, not written by the Coder.

## problem_statement

There is no small, well-tested collection of pure string helpers in this
workspace. We want a single self-contained Python package exposing a handful of
independent, standard-library-only text utilities, each fully unit-tested — a
clean multi-function target that exercises incremental, one-task-at-a-time
implementation.

## purpose_and_goals

Build **textkit**: a tiny pure-Python package under `src/textkit/` exposing four
independent, dependency-free functions, each an exact, closed specification with
its own tests. The functions are mutually independent (no shared state) so they
can be implemented one at a time and verified incrementally.

## target_users

The repo owner (Jared), as a self-contained reference/utility package. No
external users, no distribution requirements beyond a normal importable package.

## in_scope

- Package `src/textkit/__init__.py` re-exporting all four functions.
- Module `src/textkit/slugify.py` — `slugify(s: str) -> str`.
- Module `src/textkit/truncate.py` — `truncate(s: str, limit: int) -> str`.
- Module `src/textkit/word_count.py` — `word_count(s: str) -> int`.
- Module `src/textkit/is_palindrome.py` — `is_palindrome(s: str) -> bool`.
- Colocated tests under `src/textkit/tests/` — one `test_<name>.py` per
  function, covering the known cases and the error cases below.

## out_of_scope / non_goals

- No CLI, no web interface, no file/network I/O, no logging.
- No third-party dependencies (standard library only).
- No repo-root files and no top-level `tests/` directory — everything the model
  writes lives under `src/` (the `pyproject.toml` is pre-seeded).
- No Unicode normalization beyond what is specified for `slugify` below.

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
- `truncate(s, limit)`: if `len(s) <= limit`, return `s` unchanged; otherwise
  return the first `max(0, limit - 1)` characters followed by a single `"…"`
  (U+2026) so the result length is exactly `limit`. Raises `ValueError` if
  `limit < 1`; raises `TypeError` if `s` is not a `str` or `limit` is not an
  `int`. **Known cases (input → output):**
  - `("hello", 10)` → `"hello"` (already within limit)
  - `("hello world", 8)` → `"hello w…"` (7 chars + `…`, total length 8)
  - `("abc", 1)` → `"…"` (limit 1 → 0 chars + `…`)
  - `("abc", 0)` → raises `ValueError`
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
- `is_palindrome(s)`: return `True` if `s`, considering only alphanumeric
  characters and ignoring case, reads the same forwards and backwards; the
  empty string (after filtering) returns `True`. Raises `TypeError` if `s` is
  not a `str`. **Known cases (input → output):**
  - `"A man, a plan, a canal: Panama"` → `True`
  - `"racecar"` → `True`
  - `"hello"` → `False`
  - `""` → `True`; `".,!"` → `True` (no alphanumerics after filtering)

## integration_context

Standalone package. Layout: `src/textkit/` with colocated `src/textkit/tests/`.
Importable as `import textkit`. No external services, no network.

## acceptance_criteria

- `import textkit` exposes `slugify`, `truncate`, `word_count`, `is_palindrome`.
- Each function meets its specification above, including every error case.
- The full pytest suite passes (`pytest -q` from the repo root, collecting
  `src/textkit/tests/`).
- `ruff check` and `ruff format --check` are clean.

## priority_ranking

- **must_have_v1:** all four functions, their error handling, and their tests.
  All are required for v1.
- **later/nice-to-have:** none — the scope is intentionally closed.

## timeline_and_cost_estimates

A few small tasks (one per function); this is a reference utility, not a
product. No external deadline.

## risks_and_assumptions

- Assumption: Python 3.11+ standard library only; no third-party deps.
- Risk: off-by-one in `truncate` at the `limit`/`len(s)` boundary — covered
  explicitly by its tests.

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

None — the scope, interfaces, and error semantics are fully specified above.
Implement the four functions and their colocated tests as stated, one at a time.
