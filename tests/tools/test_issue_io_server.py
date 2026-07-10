"""Real `issue_io_server` stdio launch: discovery is offline (no `gh`/network) —
`list_tools` never executes a verb. Mirrors `test_github_server.py`'s
real-server-launch style. A successful launch + discovery in this
unauthenticated, network-off sandbox is itself proof the module imports
side-effect-free (a `gh` call at import time would hang or fail here)."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

from mcp import StdioServerParameters

from loop_engine.core.state import IssueRef
from loop_engine.mcp_servers import issue_io_server
from loop_engine.tools.mcp import MCPToolProvider

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SERVER_MODULE = "loop_engine.mcp_servers.issue_io_server"


def _provider() -> MCPToolProvider:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", _SERVER_MODULE], cwd=str(_REPO_ROOT)
    )
    return MCPToolProvider([params])


def test_issue_io_server_discovers_exactly_the_two_issue_verbs() -> None:
    with _provider() as provider:
        names = {t["name"] for t in provider.tools}
    assert names == {"create_issue", "read_issue"}


def test_create_issue_schema_has_expected_string_params() -> None:
    with _provider() as provider:
        schema = next(t for t in provider.tools if t["name"] == "create_issue")
    props = schema["input_schema"]["properties"]
    assert props["title"]["type"] == "string"
    assert props["body"]["type"] == "string"
    assert props["label"]["type"] == "string"
    required = set(schema["input_schema"].get("required", []))
    assert required == {"title", "body", "label"}


def test_read_issue_schema_has_expected_int_param() -> None:
    with _provider() as provider:
        schema = next(t for t in provider.tools if t["name"] == "read_issue")
    props = schema["input_schema"]["properties"]
    assert props["issue_number"]["type"] == "integer"


def test_issue_io_server_module_imports_no_keyring_or_subprocess() -> None:
    source = (
        Path(__file__).resolve().parents[2] / "src/loop_engine/mcp_servers/issue_io_server.py"
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
    create_issue.assert_called_once_with("t", "b", "l")
    assert json.loads(result) == {"number": 42, "url": "https://github.com/acme/repo/issues/42"}


def test_read_issue_verb_delegates_and_returns_view_json() -> None:
    with patch.object(issue_io_server, "_read_issue") as read_issue:
        read_issue.return_value = {"state": "OPEN", "body": "b", "comments": []}
        result = issue_io_server.read_issue(42)
    read_issue.assert_called_once_with(42)
    assert json.loads(result) == {"state": "OPEN", "body": "b", "comments": []}
