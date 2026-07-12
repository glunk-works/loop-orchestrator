# roman-numerals — Requirements Artifact (V1 verification input)

> Small, fully-specified spec for the Phase-6 V1 factory-run verification.
> Every field is a firm answer — there are no `OPEN` or `DRAFT` fields, so the
> PM stage should converge on the happy path (no human escalation).

## problem_statement

There is no small, well-tested reference library in this workspace for
converting between integers and Roman numerals. We want a single, self-contained
Python module that does the conversion both ways, with a clear, closed set of
rules and full test coverage — nothing more.

## purpose_and_goals

Build **roman-numerals**: a tiny pure-Python library exposing exactly two
functions — `to_roman(n: int) -> str` and `from_roman(s: str) -> int` — that are
exact inverses over the supported range. The library must be dependency-free
(standard library only), fully unit-tested, and lint-clean.

## target_users

The repo owner (Jared), as a self-contained reference/utility module. No external
users, no distribution requirements beyond a normal importable Python package.

## in_scope

- A single module `src/roman_numerals/converter.py` exposing `to_roman` and
  `from_roman`.
- A package `src/roman_numerals/__init__.py` re-exporting both functions.
- A `tests/test_converter.py` suite covering: known conversions, round-trip
  identity over the whole supported range, and the error cases below.

## out_of_scope / non_goals

- No CLI, no web interface, no I/O, no logging.
- No numbers outside 1..3999 (classical Roman numerals have no zero and no
  standard form above 3999).
- No support for alternate/medieval numeral forms (e.g. `IIII` for 4). Only the
  standard subtractive forms are accepted.
- No third-party dependencies.

## functional_requirements

- Packaging: `pyproject.toml` must configure pytest to import the package from
  the src layout **without** an editable install — set
  `[tool.pytest.ini_options] pythonpath = ["src"]` so `pytest` from the repo root
  can `import roman_numerals` directly. (The test sandbox runs `pytest` against a
  non-installed working tree; do not rely on `pip install -e .`.)
- `to_roman(n)` accepts an `int` in the inclusive range 1..3999 and returns the
  standard uppercase Roman-numeral string (subtractive form: 4=`IV`, 9=`IX`,
  40=`XL`, 90=`XC`, 400=`CD`, 900=`CM`).
- `from_roman(s)` accepts a valid standard uppercase Roman-numeral string and
  returns the corresponding `int`. It is the exact inverse of `to_roman` over
  1..3999.
- Round-trip identity: for every `n` in 1..3999, `from_roman(to_roman(n)) == n`.
- `to_roman` raises `ValueError` for non-int input or an int outside 1..3999.
- `from_roman` raises `ValueError` for input that is not a valid standard Roman
  numeral (empty string, unknown characters, or a non-canonical form such as
  `IIII` or `IC`).

## integration_context

Standalone package. Directory layout: `src/roman_numerals/`, `tests/` at repo
root. Importable as `import roman_numerals`. No external services, no network.

## acceptance_criteria

- `import roman_numerals; roman_numerals.to_roman(1994) == "MCMXCIV"` and
  `roman_numerals.from_roman("MCMXCIV") == 1994`.
- The full pytest suite passes (`pytest -q`) with tests covering known values,
  full-range round-trip identity, and every error case above.
- `ruff check` and `ruff format --check` are clean.

## priority_ranking

- **must_have_v1:** `to_roman`, `from_roman`, round-trip identity, the error
  handling above, and the test suite. All are required for v1.
- **later/nice-to-have:** none — the scope is intentionally closed.

## timeline_and_cost_estimates

Single small sprint; this is a reference utility, not a product. No external
deadline.

## risks_and_assumptions

- Assumption: Python 3.11+ standard library only; no third-party deps.
- Risk: off-by-one at the range boundaries (0, 4000) — covered explicitly by the
  error-case tests.

## security_and_risk_considerations

Pure computation over in-memory strings/ints. No secrets, no I/O, no network, no
credentials. Standard repo lint/format/SBOM gates apply; nothing library-specific.

## regulatory_and_compliance_constraints

None.

## supply_chain_security_expectations

Standard-library only; no dependencies to audit. Normal ruff + SBOM gates apply.

## cost_sensitivity

Low. This is a tiny utility; no runtime cost concerns.

## open_questions_for_architect

None — the scope, interface, range, and error semantics are fully specified
above. Implement the two functions and their tests as stated.
