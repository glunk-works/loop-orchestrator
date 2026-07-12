"""`loop_engine.mcp.json` schema + loader — config-driven, consumer-scoped MCP
server discovery (Phase 5, cross-cutting #3).

Named `loop_engine.mcp.json` (not `.mcp.json`) because repo-root `.mcp.json` is
already Claude Code's own project MCP config (a different schema/purpose — the
devcontainer's hosted-github wiring); loop-engine owns a distinct, namespaced
file for its own stdio server-launch specs.

Optional, in-repo, trusted config file: `{"servers": {"<name>": {"command":
str, "args": [str, ...], "cwd": str | None}}}`. Read-only (`Path.read_text` +
`json.loads`, never `eval`/`yaml.load`) — `tools/mcp` still writes no files and
adds no subprocess/credential surface. Absence of the file must be
byte-identical to the one hard-coded `coder_tools` server this module
generalizes — the built-in default below.
"""

from __future__ import annotations

import json
import sys
from functools import cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

_CONFIG_FILENAME = "loop_engine.mcp.json"
_CODER_TOOLS_SERVER_MODULE = "loop_engine.mcp_servers.coder_tools_server"

CODER_TOOLS_SERVER_NAME = "coder_tools"
# The github factory-verb server's logical name in loop_engine.mcp.json — no
# built-in default (unlike coder_tools): it exists only via the committed
# repo-root config's static launch spec.
GITHUB_SERVER_NAME = "github"
# The issue escalation-verb server's logical name in loop_engine.mcp.json — same
# posture as GITHUB_SERVER_NAME: no built-in default, exists only via the
# committed repo-root config's static launch spec.
ISSUE_SERVER_NAME = "issue"


class MCPServerSpec(BaseModel):
    """One logical server's static launch spec, as declared in `loop_engine.mcp.json`.

    `command`/`args` only (no `shell=True`, no arbitrary shell strings) —
    consistent with every existing launch in this module.
    """

    model_config = ConfigDict(extra="forbid")

    command: str = Field(min_length=1)
    args: list[str]
    cwd: str | None = None


class MCPConfigFile(BaseModel):
    """The `loop_engine.mcp.json` top-level shape."""

    model_config = ConfigDict(extra="forbid")

    servers: dict[str, MCPServerSpec] = Field(default_factory=dict)


@cache
def _repo_root() -> Path:
    """Repo root, found by walking up to the `pyproject.toml` marker — anchors
    `loop_engine.mcp.json` resolution independent of `Path.cwd()`, which worktree
    isolation `chdir`s elsewhere."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return here.parents[4]


def _default_servers() -> dict[str, MCPServerSpec]:
    """The built-in `coder_tools` entry — the local-mode launch of the
    coder-tools stdio server (this is the single source of truth for it; the
    pre-22a `coder_tools_server_params()` helper it replaced is gone). `cwd` is left `None` here;
    it is supplied per-call (by `build_provider_for`/`build_coder_tool_provider`),
    not fixed at config-load time."""
    return {
        CODER_TOOLS_SERVER_NAME: MCPServerSpec(
            command=sys.executable,
            args=["-m", _CODER_TOOLS_SERVER_MODULE],
            cwd=None,
        )
    }


def load_mcp_config(path: str | Path | None = None) -> dict[str, MCPServerSpec]:
    """Load `loop_engine.mcp.json` (repo root, unless `path` overrides — tests use this).

    Absent file -> the built-in default only (one `coder_tools` entry).
    Present file -> merged over the default by logical server name: an
    explicit `coder_tools` entry overrides the built-in local profile; other
    names are added alongside it.
    """
    config_path = Path(path) if path is not None else _repo_root() / _CONFIG_FILENAME
    servers = _default_servers()
    if not config_path.is_file():
        return servers
    raw = config_path.read_text(encoding="utf-8")
    parsed = MCPConfigFile.model_validate(json.loads(raw))
    for name, spec in parsed.servers.items():
        # R7: a committed stanza's bare "python" is a launch-side alias for
        # "the active interpreter" (matching the coder_tools built-in below),
        # not a literal PATH lookup — a python3-only host has no `python`.
        if spec.command == "python":
            parsed.servers[name] = spec.model_copy(update={"command": sys.executable})
    servers.update(parsed.servers)
    return servers
