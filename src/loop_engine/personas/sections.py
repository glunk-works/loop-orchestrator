"""Merge targeted section corrections into a prior markdown artifact.

Revision passes ask the model for ONLY the corrected sections; `merge` folds
them into the previous artifact so untouched sections stay byte-identical and
the run never pays to regenerate a whole document.

Sections are delimited by `##`/`###` header lines (both levels, so coder
reports' `### FILEPATH:` blocks and documents' `## Section` headings are each
addressable units). Corrections naming a header the previous artifact does
not contain are rejected and logged — merges stay deterministic.
"""

import logging
import re

logger = logging.getLogger(__name__)

_SECTION_HEADER_RE = re.compile(r"^#{2,3} .+$", re.MULTILINE)


def _split(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Split into (preamble, [(header_line, section_text)]).

    Each section's text runs from its header line to the next header (or end
    of text), so reassembling preamble + sections reproduces `text` exactly.
    """
    matches = list(_SECTION_HEADER_RE.finditer(text))
    if not matches:
        return text, []
    preamble = text[: matches[0].start()]
    sections = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((match.group(0).strip(), text[match.start() : end]))
    return preamble, sections


def has_sections(text: str) -> bool:
    """Whether `text` has any addressable section headers.

    An artifact without them cannot receive targeted corrections — callers
    fall back to full regeneration instead of a merge that can only no-op.
    """
    return _SECTION_HEADER_RE.search(text) is not None


def merge(previous: str, corrections: str) -> str:
    """Replace sections of `previous` named by header in `corrections`.

    Untouched sections (and the preamble) are preserved byte-identically, in
    their original order. Corrections referencing unknown headers are
    rejected and logged, never appended. Pure function — no I/O.
    """
    _, corrected_sections = _split(corrections)
    preamble, previous_sections = _split(previous)
    known_headers = {header for header, _ in previous_sections}

    replacements: dict[str, str] = {}
    for header, section in corrected_sections:
        if header not in known_headers:
            logger.warning("correction references unknown section %r; rejected", header)
            continue
        # A replaced section must still end in a newline when another section
        # follows it, or the next header would fuse onto its last line.
        replacements[header] = section if section.endswith("\n") else section + "\n"

    merged: list[str] = [preamble]
    for index, (header, section) in enumerate(previous_sections):
        if header in replacements:
            replacement = replacements[header]
            if index == len(previous_sections) - 1:
                replacement = replacement.rstrip("\n") + ("\n" if section.endswith("\n") else "")
            merged.append(replacement)
        else:
            merged.append(section)
    return "".join(merged)
