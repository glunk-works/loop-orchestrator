"""End-to-end MCP tests: spawn the real coder-tools stdio server and assert the
provider discovers its tools and dispatches to the same results as the
in-process implementations."""

import os

import pytest

from loop_engine.tools.coder_tools import grep, list_files, read_file
from loop_engine.tools.mcp import (
    MCPToolError,
    build_coder_tool_provider,
    use_mcp_tools,
)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def _seeded_tree(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "foo.md").write_text("hello from docs\nsecond line\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_text("def add(a, b):\n    return a + b\n")
    (tmp_path / "src" / "test_mod.py").write_text(
        "from mod import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"
    )
    return tmp_path


@pytest.fixture
def _provider(_seeded_tree):
    with build_coder_tool_provider(cwd=_seeded_tree) as provider:
        yield provider


def test_provider_discovers_all_coder_tools(_provider) -> None:
    names = {t["name"] for t in _provider.tools}
    assert names == {"read_file", "list_files", "grep", "run_tests"}
    read_schema = next(t for t in _provider.tools if t["name"] == "read_file")
    assert read_schema["input_schema"]["properties"]["path"]["type"] == "string"


def test_read_file_dispatch_matches_in_process(_provider) -> None:
    assert _provider.execute("read_file", {"path": "docs/foo.md"}) == read_file("docs/foo.md")


def test_list_files_dispatch_matches_in_process(_provider) -> None:
    assert _provider.execute("list_files", {"path": "src"}) == list_files("src")


def test_grep_dispatch_matches_in_process(_provider) -> None:
    out = _provider.execute("grep", {"pattern": r"def add", "path": "src"})
    assert out == grep(r"def add", "src")
    assert "mod.py" in out


def test_run_tests_dispatch_runs_pytest(_provider) -> None:
    out = _provider.execute("run_tests", {"path": "src"})
    assert "pytest exit code: 0" in out


def test_error_result_raises_mcp_tool_error(_provider) -> None:
    with pytest.raises(MCPToolError):
        _provider.execute("read_file", {"path": "docs/missing.md"})


def test_unknown_tool_raises_mcp_tool_error(_provider) -> None:
    with pytest.raises(MCPToolError):
        _provider.execute("does_not_exist", {})


def test_use_mcp_tools_flag(monkeypatch) -> None:
    monkeypatch.delenv("LOOP_ENGINE_TOOLS", raising=False)
    assert use_mcp_tools() is False
    monkeypatch.setenv("LOOP_ENGINE_TOOLS", "mcp")
    assert use_mcp_tools() is True


def test_traversal_path_is_rejected_by_server(_provider) -> None:
    with pytest.raises(MCPToolError):
        _provider.execute("read_file", {"path": "../../etc/passwd"})
    assert not os.path.exists("etc")
