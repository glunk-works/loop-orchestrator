"""Read-only filesystem tools for the agentic Coder persona.

Every path argument is model-controlled input: each tool validates it with
the same rules as the write side (`tools/state_io`) — relative, under an
allowed artifact root, no traversal — plus a post-resolution symlink-escape
check. Reads use Path.read_text only (bare open() is reserved to
tools/state_io by the AST boundary test). No module here touches keyring.
"""

import re
from pathlib import Path

from loop_engine.tools.state_io.writer import validate_artifact_relative_path

# Tool results feed straight back into the model's context window: cap them.
MAX_RESULT_CHARS = 20_000

# The model-facing tool schemas are NOT declared here: `mcp_servers/
# coder_tools_server.py` re-fronts these functions over MCP and FastMCP derives
# each schema from the function signature + docstring. The hand-written schema
# dicts this module used to export existed only for the in-process tool dispatch,
# which Phase 6 deleted.


def truncate_result(text: str) -> str:
    if len(text) <= MAX_RESULT_CHARS:
        return text
    return text[:MAX_RESULT_CHARS] + "\n... [truncated]"


def resolve_tool_path(relative_path: str) -> Path:
    """Validate a model-supplied path and resolve it inside the run tree.

    Reuses the state_io traversal rules, then rejects symlink escapes the
    lexical check cannot see.
    """
    posix_path = validate_artifact_relative_path(relative_path)
    path = Path(*posix_path.parts)
    if path.exists() and not path.resolve().is_relative_to(Path.cwd().resolve()):
        raise ValueError(f"Invalid artifact path: {relative_path!r} escapes the run tree")
    return path


def read_file(path: str) -> str:
    target = resolve_tool_path(path)
    if not target.is_file():
        raise ValueError(f"No such file: {path!r}")
    return truncate_result(target.read_text(encoding="utf-8", errors="replace"))


def list_files(path: str) -> str:
    target = resolve_tool_path(path)
    if not target.is_dir():
        raise ValueError(f"No such directory: {path!r}")
    entries = sorted(str(entry) for entry in target.rglob("*") if entry.is_file())
    return truncate_result("\n".join(entries) or "(empty)")


def grep(pattern: str, path: str) -> str:
    compiled = re.compile(pattern)
    target = resolve_tool_path(path)
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(entry for entry in target.rglob("*") if entry.is_file())
    else:
        raise ValueError(f"No such file or directory: {path!r}")

    matches: list[str] = []
    for file in files:
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if compiled.search(line):
                matches.append(f"{file}:{line_number}:{line}")
    return truncate_result("\n".join(matches) or "(no matches)")
