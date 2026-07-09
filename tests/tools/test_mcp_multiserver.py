"""Multi-server discovery + routing through the real `MCPToolProvider`
(sprint 22a, Task 3 — proves cross-cutting #3 is paid down). Two hermetic,
offline stdio server fixtures stand in for a `loop_engine.mcp.json` declaring
more than one server; the coder-tools server itself is exercised separately
in `test_mcp_provider.py`."""

import json
import sys
from pathlib import Path

import pytest
from mcp import StdioServerParameters

from loop_engine.tools.mcp import MCPToolError, MCPToolProvider
from loop_engine.tools.mcp.config import load_mcp_config

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def _two_server_config(tmp_path):
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": {
                    "echo": {
                        "command": sys.executable,
                        "args": ["-m", "tests.tools.fixtures.echo_server"],
                        "cwd": str(_REPO_ROOT),
                    },
                    "greet": {
                        "command": sys.executable,
                        "args": ["-m", "tests.tools.fixtures.greet_server"],
                        "cwd": str(_REPO_ROOT),
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _server_params(config_path, names) -> list[StdioServerParameters]:
    servers = load_mcp_config(config_path)
    return [
        StdioServerParameters(
            command=servers[name].command, args=servers[name].args, cwd=servers[name].cwd
        )
        for name in names
    ]


def test_two_server_discovery_and_routing(_two_server_config) -> None:
    params = _server_params(_two_server_config, ["echo", "greet"])
    with MCPToolProvider(params) as provider:
        names = {t["name"] for t in provider.tools}
        assert names == {"ping", "greet"}
        assert provider.execute("ping", {"message": "hi"}) == "echo:hi"
        assert provider.execute("greet", {"name": "world"}) == "hello, world"
        with pytest.raises(MCPToolError):
            provider.execute("does_not_exist", {})
        thread = provider._thread

    assert thread is not None
    assert not thread.is_alive()
