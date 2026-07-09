"""`.mcp.json` schema + loader — config-driven, consumer-scoped MCP server
discovery (Phase 5, cross-cutting #3).

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

_CONFIG_FILENAME = ".mcp.json"
_CODER_TOOLS_SERVER_MODULE = "loop_engine.mcp_servers.coder_tools_server"

CODER_TOOLS_SERVER_NAME = "coder_tools"


class MCPServerSpec(BaseModel):
    """One logical server's static launch spec, as declared in `.mcp.json`.

    `command`/`args` only (no `shell=True`, no arbitrary shell strings) —
    consistent with every existing launch in this module.
    """

    model_config = ConfigDict(extra="forbid")

    command: str = Field(min_length=1)
    args: list[str]
    cwd: str | None = None


class MCPConfigFile(BaseModel):
    """The `.mcp.json` top-level shape."""

    model_config = ConfigDict(extra="forbid")

    servers: dict[str, MCPServerSpec] = Field(default_factory=dict)


@cache
def _repo_root() -> Path:
    """Repo root, found by walking up to the `pyproject.toml` marker — anchors
    `.mcp.json` resolution independent of `Path.cwd()`, which worktree
    isolation `chdir`s elsewhere."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return here.parents[4]


def _default_servers() -> dict[str, MCPServerSpec]:
    """The built-in `coder_tools` entry — equivalent to today's hard-coded
    `coder_tools_server_params()` local-mode launch. `cwd` is left `None` here;
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
    """Load `.mcp.json` (repo root, unless `path` overrides — tests use this).

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
    servers.update(parsed.servers)
    return servers
