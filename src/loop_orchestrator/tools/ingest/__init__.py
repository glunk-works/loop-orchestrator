"""The ingestion-sanitization seam (bounty loop, §10; P0-D6) -- a
structural/mechanical normalizer for attacker-influenceable scanner/target
text before it reaches the triage LLM. A pure leaf: no live consumer yet, no
`keyring`/`psycopg`/`subprocess`, no file writes.
"""

from loop_orchestrator.tools.ingest.sanitize import DEFAULT_MAX_LEN, sanitize

__all__ = [
    "DEFAULT_MAX_LEN",
    "sanitize",
]
