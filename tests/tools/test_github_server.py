"""Real `github_server` stdio launch: discovery is offline (no `gh`/network) —
`list_tools` never executes a verb. Mirrors `test_mcp_provider.py`'s
real-server-launch style for `coder_tools_server`. A successful launch +
discovery in this unauthenticated, network-off sandbox is itself proof the
module imports side-effect-free (a `gh` call at import time would hang or
fail here)."""

import sys
from pathlib import Path

from mcp import StdioServerParameters

from loop_engine.tools.mcp import MCPToolProvider

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SERVER_MODULE = "loop_engine.mcp_servers.github_server"


def _provider() -> MCPToolProvider:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", _SERVER_MODULE], cwd=str(_REPO_ROOT)
    )
    return MCPToolProvider([params])


def test_github_server_discovers_exactly_the_four_factory_verbs() -> None:
    with _provider() as provider:
        names = {t["name"] for t in provider.tools}
    assert names == {"create_repository", "clone_repo", "create_branch", "open_pr"}


def test_clone_repo_schema_has_expected_string_params() -> None:
    with _provider() as provider:
        schema = next(t for t in provider.tools if t["name"] == "clone_repo")
    props = schema["input_schema"]["properties"]
    assert props["slug"]["type"] == "string"
    assert props["dest"]["type"] == "string"


def test_create_repository_schema_has_expected_params() -> None:
    with _provider() as provider:
        schema = next(t for t in provider.tools if t["name"] == "create_repository")
    props = schema["input_schema"]["properties"]
    assert props["name"]["type"] == "string"
    assert "org" in props
    assert "private" in props


def test_open_pr_schema_requires_all_six_fields() -> None:
    with _provider() as provider:
        schema = next(t for t in provider.tools if t["name"] == "open_pr")
    required = set(schema["input_schema"].get("required", []))
    assert required == {"owner", "repo", "head", "base", "title", "body"}
