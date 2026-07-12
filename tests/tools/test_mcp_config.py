"""`loop_engine.mcp.json` loader: default fallback, merge-over-default, validation."""

import json
import sys

import pytest
from pydantic import ValidationError

from loop_engine.tools.mcp.config import CODER_TOOLS_SERVER_NAME, load_mcp_config


def test_absent_file_yields_builtin_coder_tools_default(tmp_path) -> None:
    servers = load_mcp_config(tmp_path / "does_not_exist.json")
    assert set(servers) == {CODER_TOOLS_SERVER_NAME}
    spec = servers[CODER_TOOLS_SERVER_NAME]
    assert spec.command == sys.executable
    assert spec.args == ["-m", "loop_engine.mcp_servers.coder_tools_server"]
    assert spec.cwd is None


def test_present_file_adds_a_second_server(tmp_path) -> None:
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps({"servers": {"github": {"command": "github-server", "args": ["--stdio"]}}}),
        encoding="utf-8",
    )
    servers = load_mcp_config(config_path)
    assert set(servers) == {CODER_TOOLS_SERVER_NAME, "github"}
    assert servers["github"].command == "github-server"
    assert servers["github"].args == ["--stdio"]


def test_explicit_coder_tools_entry_overrides_builtin_default(tmp_path) -> None:
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": {
                    CODER_TOOLS_SERVER_NAME: {"command": "custom-python", "args": ["-m", "x"]}
                }
            }
        ),
        encoding="utf-8",
    )
    servers = load_mcp_config(config_path)
    assert set(servers) == {CODER_TOOLS_SERVER_NAME}
    assert servers[CODER_TOOLS_SERVER_NAME].command == "custom-python"
    assert servers[CODER_TOOLS_SERVER_NAME].args == ["-m", "x"]


def test_unknown_key_raises_validation_error(tmp_path) -> None:
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps({"servers": {"github": {"command": "x", "args": [], "bogus": True}}}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_mcp_config(config_path)


def test_missing_command_raises_validation_error(tmp_path) -> None:
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps({"servers": {"github": {"args": ["--stdio"]}}}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_mcp_config(config_path)


def test_missing_args_raises_validation_error(tmp_path) -> None:
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps({"servers": {"github": {"command": "x"}}}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_mcp_config(config_path)


def test_top_level_unknown_key_raises_validation_error(tmp_path) -> None:
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(json.dumps({"servers": {}, "bogus": True}), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_mcp_config(config_path)


def test_bare_python_command_is_substituted_with_sys_executable(tmp_path) -> None:
    """R7: a committed stanza's bare "python" must not fail to spawn on a
    python3-only host — substituted at launch time, matching the
    `coder_tools` built-in default."""
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": {
                    "issue": {
                        "command": "python",
                        "args": ["-m", "loop_engine.mcp_servers.issue_io_server"],
                    },
                    "github": {
                        "command": "python",
                        "args": ["-m", "loop_engine.mcp_servers.github_server"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    servers = load_mcp_config(config_path)
    assert servers["issue"].command == sys.executable
    assert servers["github"].command == sys.executable


def test_non_python_command_is_left_untouched(tmp_path) -> None:
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps({"servers": {"github": {"command": "github-server", "args": ["--stdio"]}}}),
        encoding="utf-8",
    )
    servers = load_mcp_config(config_path)
    assert servers["github"].command == "github-server"
