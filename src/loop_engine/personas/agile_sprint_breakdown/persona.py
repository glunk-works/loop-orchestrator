"""Sprint-block parsing that outlives the classic `AgileSprintBreakdownPersona`.

Phase 6 deleted the persona class and its embedded prompt template (the prompt
now lives only in `prompts/03_agile_sprint_breakdown_prompt.md`, which the
declarative `SprintBreakdownGenerator` config loads).

`_parse_sprint_blocks` remains because `personas/declarative/services.py` reuses
it verbatim — it is the parser that splits a breakdown response into one file
per sprint, and reusing it (rather than re-implementing) is what kept the
declarative output byte-identical to the classic persona's.
"""

import re

_FILEPATH_HEADER_RE = re.compile(r"^### FILEPATH:\s*(\S+)\s*$", re.MULTILINE)


def _parse_sprint_blocks(text: str) -> list[dict[str, str]]:
    matches = list(_FILEPATH_HEADER_RE.finditer(text))
    blocks = []
    for i, match in enumerate(matches):
        path = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        # Drop the "---" divider the output format places between sprint
        # files; it belongs to the response framing, not the file content.
        if content.endswith("\n---"):
            content = content[: -len("\n---")].rstrip()
        blocks.append({"path": path, "content": content})
    return blocks
