"""Real `issue_io_server` stdio launch: discovery is offline (no `gh`/network) —
`list_tools` never executes a verb. Mirrors `test_github_server.py`'s
real-server-launch style. A successful launch + discovery in this
unauthenticated, network-off sandbox is itself proof the module imports
side-effect-free (a `gh` call at import time would hang or fail here)."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp import StdioServerParameters

from loop_orchestrator.core.state import IssueRef
from loop_orchestrator.mcp_servers import issue_io_server
from loop_orchestrator.tools.mcp import MCPToolProvider

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SERVER_MODULE = "loop_orchestrator.mcp_servers.issue_io_server"


# Module-scoped: every test here is discovery-only (schema checks against an
# offline, no-`gh`-call server), so one real launch is amortized across the
# whole file instead of paid per test (Sprint 37 Task 2).
@pytest.fixture(scope="module")
def _provider():
    params = StdioServerParameters(
        command=sys.executable, args=["-m", _SERVER_MODULE], cwd=str(_REPO_ROOT)
    )
    with MCPToolProvider([params]) as provider:
        yield provider


def test_issue_io_server_discovers_exactly_the_two_issue_verbs(_provider) -> None:
    names = {t["name"] for t in _provider.tools}
    assert names == {"create_issue", "read_issue"}


def test_create_issue_schema_has_expected_string_params(_provider) -> None:
    schema = next(t for t in _provider.tools if t["name"] == "create_issue")
    props = schema["input_schema"]["properties"]
    assert props["title"]["type"] == "string"
    assert props["body"]["type"] == "string"
    assert props["label"]["type"] == "string"
    assert "repo" in props
    required = set(schema["input_schema"].get("required", []))
    assert required == {"title", "body", "label"}


def test_read_issue_schema_has_expected_int_param(_provider) -> None:
    schema = next(t for t in _provider.tools if t["name"] == "read_issue")
    props = schema["input_schema"]["properties"]
    assert props["issue_number"]["type"] == "integer"
    assert "repo" in props


def test_issue_io_server_module_imports_no_keyring_or_subprocess() -> None:
    source = (
        Path(__file__).resolve().parents[2] / "src/loop_orchestrator/mcp_servers/issue_io_server.py"
    ).read_text(encoding="utf-8")
    assert "keyring" not in source
    assert "import subprocess" not in source


def test_create_issue_verb_delegates_and_returns_issue_ref_json() -> None:
    """In-process (not the stdio subprocess): the `@mcp.tool()`-decorated
    function is a plain callable, so `tools/issue_io.create_issue` can be
    monkeypatched here — the hermetic dispatch check the sprint plan asks for,
    without a real `gh` and without a subprocess boundary in the way."""
    with patch.object(issue_io_server, "_create_issue") as create_issue:
        create_issue.return_value = IssueRef(
            number=42, url="https://github.com/acme/repo/issues/42"
        )
        result = issue_io_server.create_issue("t", "b", "l")
    create_issue.assert_called_once_with("t", "b", "l", repo=None)
    assert json.loads(result) == {"number": 42, "url": "https://github.com/acme/repo/issues/42"}


def test_create_issue_verb_forwards_explicit_repo() -> None:
    with patch.object(issue_io_server, "_create_issue") as create_issue:
        create_issue.return_value = IssueRef(
            number=42, url="https://github.com/acme/repo/issues/42"
        )
        issue_io_server.create_issue("t", "b", "l", repo="acme/repo")
    create_issue.assert_called_once_with("t", "b", "l", repo="acme/repo")


def test_read_issue_verb_delegates_and_returns_view_json() -> None:
    with patch.object(issue_io_server, "_read_issue") as read_issue:
        read_issue.return_value = {"state": "OPEN", "body": "b", "comments": []}
        result = issue_io_server.read_issue(42)
    read_issue.assert_called_once_with(42, repo=None)
    assert json.loads(result) == {"state": "OPEN", "body": "b", "comments": []}
