"""End-to-end MCP tests: spawn the real coder-tools stdio server and assert the
provider discovers its tools and dispatches to the same results as the
in-process implementations."""

import json
import os

import pytest

from loop_engine.tools.coder_tools import grep, list_files, read_file
from loop_engine.tools.mcp import (
    CODER_TOOLS_SERVER_NAME,
    GITHUB_SERVER_NAME,
    ISSUE_SERVER_NAME,
    MCPToolError,
    build_coder_tool_provider,
    build_github_provider,
    build_issue_provider,
    load_mcp_config,
    use_mcp_tools,
)
from loop_engine.tools.mcp import config as mcp_config


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


def test_extra_config_server_never_reaches_coder_provider(
    monkeypatch, tmp_path, _seeded_tree
) -> None:
    """Even when `loop_engine.mcp.json` declares a `github`-like server
    alongside `coder_tools`, the coder consumer's provider must expose exactly
    the four coder tools — the extra server is never selected/launched. This
    encodes cross-cutting #2's "orchestrator-invoked, not model tools" as an
    enforced invariant before the github server exists (22b)."""
    config_path = tmp_path / "loop_engine.mcp.json"
    config_path.write_text(
        json.dumps(
            {"servers": {"github": {"command": "github-server-not-installed", "args": ["--stdio"]}}}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mcp_config, "_repo_root", lambda: tmp_path)
    with build_coder_tool_provider(cwd=_seeded_tree) as provider:
        names = {t["name"] for t in provider.tools}
    assert names == {"read_file", "list_files", "grep", "run_tests"}


def test_committed_config_declares_github_and_issue_alongside_coder_tools() -> None:
    """The real, committed repo-root `loop_engine.mcp.json` (22b Task 3, 26
    Task 2) — `load_mcp_config()` with no override reads it for real."""
    servers = load_mcp_config()
    assert set(servers) == {CODER_TOOLS_SERVER_NAME, GITHUB_SERVER_NAME, ISSUE_SERVER_NAME}
    assert servers[GITHUB_SERVER_NAME].args == ["-m", "loop_engine.mcp_servers.github_server"]
    assert servers[ISSUE_SERVER_NAME].args == ["-m", "loop_engine.mcp_servers.issue_io_server"]


def test_committed_github_stanza_does_not_change_coder_provider_tool_set(_provider) -> None:
    """With the committed `github`/`issue` stanzas in effect (no override
    here), the coder consumer's provider is still exactly the four coder
    tools."""
    names = {t["name"] for t in _provider.tools}
    assert names == {"read_file", "list_files", "grep", "run_tests"}


def test_build_github_provider_discovers_exactly_four_github_verbs() -> None:
    with build_github_provider() as provider:
        names = {t["name"] for t in provider.tools}
    assert names == {"create_repository", "clone_repo", "create_branch", "open_pr"}


def test_build_issue_provider_discovers_exactly_two_issue_verbs() -> None:
    with build_issue_provider() as provider:
        names = {t["name"] for t in provider.tools}
    assert names == {"create_issue", "read_issue"}


def test_coder_github_and_issue_providers_are_pairwise_disjoint(_provider) -> None:
    """Cross-cutting #2, extended two-way -> three-way (26 Task 5): with the
    committed `loop_engine.mcp.json` in effect, the model's coder-tool
    provider and the orchestrator's github/issue providers expose exactly
    their own tools each, and no pair of sets intersects."""
    coder_names = {t["name"] for t in _provider.tools}
    with build_github_provider() as github_provider:
        github_names = {t["name"] for t in github_provider.tools}
    with build_issue_provider() as issue_provider:
        issue_names = {t["name"] for t in issue_provider.tools}

    assert coder_names == {"read_file", "list_files", "grep", "run_tests"}
    assert github_names == {"create_repository", "clone_repo", "create_branch", "open_pr"}
    assert issue_names == {"create_issue", "read_issue"}
    assert coder_names.isdisjoint(github_names)
    assert coder_names.isdisjoint(issue_names)
    assert github_names.isdisjoint(issue_names)
