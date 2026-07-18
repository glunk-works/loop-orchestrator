"""Top-level orchestrator-level flows (Phase 5 piece 3+): end-to-end callers
that chain `tools/repo_io` + `tools/git_io` + the default loop over a target
repo. A sibling of `cli.py`/`trigger/` — not a `tools/` module, not an MCP
server. See `tests/flows/test_boundaries.py` for the enforced posture.
"""
