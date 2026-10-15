"""The recon JSONL parser (S47-D5/T2): turns `bounty-infra`'s
subfinder/httpx/nuclei scan output into typed `ReconRecord`s, one per line.

This is the point where fully untrusted, attacker-influenceable bytes first
enter the process (S10). `ReconRecord` is a **whitelisted-fields-only**
extraction (S43's "structured extraction + wrap"): `extra="ignore"` means an
unrecognized key from the upstream payload is silently dropped, never
round-tripped into `inventory_db` or any later prompt.

Fail-closed per S47-D5: the payload as a whole failing to decode as text is
the **wholesale** failure and raises `ReconPayloadError`; a single line that
isn't valid JSON, isn't a JSON object, or is missing/mistyped `host` is
**dropped and counted**, never raised -- one bad scanner line must not sink
an otherwise-good batch.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ReconRecord(BaseModel):
    """One scanner-emitted JSONL line, reduced to whitelisted typed fields.

    `host` is the only required field (the scope/DB join key). Everything
    else is scanner-observation data: `port`/`path`/`http_methods` describe
    an endpoint on that host (a record with no `path` is host-only, e.g. a
    bare subfinder hit); `title`/`webserver`/`tech`/`matched_at` are
    target-derived free text (httpx page title + server banner, detected
    tech stack, nuclei's `matched-at` -- the `bounty-infra#13` vuln field)
    that must be `sanitize`d before it reaches `inventory_db`, let alone a
    triage LLM.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    host: str
    port: int | None = None
    path: str | None = None
    http_methods: list[str] = []
    title: str | None = None
    webserver: str | None = None
    tech: list[str] = []
    matched_at: str | None = Field(default=None, alias="matched-at")


class ReconPayloadError(Exception):
    """The recon S3 payload could not be read as text at all -- the
    wholesale-unparseable case (S47-D5), distinct from a single bad line."""


def parse_jsonl(payload: bytes) -> tuple[list[ReconRecord], int]:
    """Parse a recon JSONL payload into typed `ReconRecord`s.

    Returns `(records, malformed_line_count)`. A line that fails JSON
    decoding, isn't a JSON object, or fails `ReconRecord` validation (e.g.
    a missing/non-string `host`) is dropped and counted rather than
    raised -- only a payload that isn't valid UTF-8 text raises
    `ReconPayloadError`.
    """
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReconPayloadError(f"recon payload is not valid UTF-8 text: {exc}") from exc

    records: list[ReconRecord] = []
    malformed_line_count = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        record = _parse_line(line)
        if record is None:
            malformed_line_count += 1
        else:
            records.append(record)
    return records, malformed_line_count


def _parse_line(line: str) -> ReconRecord | None:
    try:
        raw: Any = json.loads(line)
    except json.JSONDecodeError:
        return None
    except (RecursionError, ValueError):
        # A crafted line -- pathologically deep nesting (`RecursionError`)
        # or an oversized integer literal past `sys.int_info`'s string-to-int
        # digit limit (a bare `ValueError`, not a `JSONDecodeError`) -- must
        # drop+count like any other malformed line, never escape and sink
        # the whole batch (S47-D5's fail-closed contract is per-line, not
        # per-payload, for anything short of an undecodable payload).
        return None
    if not isinstance(raw, dict):
        return None
    try:
        return ReconRecord.model_validate(raw)
    except ValidationError:
        return None
