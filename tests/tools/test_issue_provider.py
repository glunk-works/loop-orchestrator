"""`build_issue_provider()` (real stdio launch, discovery only) and the
`mcp_issue_filer`/`mcp_issue_reader` client adapters (against a fake provider —
no real `gh`, no subprocess)."""

import json
from pathlib import Path

from loop_engine.core.state import IssueRef, Question, State
from loop_engine.tools.issue_io import (
    default_issue_filer,
    default_issue_reader,
    mcp_issue_filer,
    mcp_issue_reader,
)
from loop_engine.tools.mcp import ISSUE_SERVER_NAME, build_issue_provider


def test_build_issue_provider_discovers_exactly_the_two_issue_verbs() -> None:
    with build_issue_provider() as provider:
        names = {t["name"] for t in provider.tools}
    assert names == {"create_issue", "read_issue"}


def test_issue_server_name_is_issue() -> None:
    assert ISSUE_SERVER_NAME == "issue"


def test_mcp_client_adapter_module_imports_no_keyring() -> None:
    source = (
        Path(__file__).resolve().parents[2] / "src/loop_engine/tools/issue_io/mcp_client.py"
    ).read_text(encoding="utf-8")
    assert "keyring" not in source


class _FakeProvider:
    """Records dispatched verb calls and returns canned JSON — stands in for
    an entered `MCPToolProvider` without spawning a subprocess."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self) -> "_FakeProvider":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def execute(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        if name == "create_issue":
            return IssueRef(
                number=17, url="https://github.com/acme/repo/issues/17"
            ).model_dump_json()
        if name == "read_issue":
            return json.dumps({"state": "OPEN", "body": "b", "comments": []})
        raise AssertionError(f"unexpected verb: {name}")


def _state() -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts={})


def _questions() -> list[Question]:
    return [Question(id="q1", origin_stage="ArchitecturePersona", text="Which region?")]


def test_mcp_issue_filer_renders_locally_and_dispatches_create_issue() -> None:
    provider = _FakeProvider()
    filer = mcp_issue_filer(provider)

    ref = filer(_state(), _questions(), "state/run-1/01_awaiting_issue.json")

    assert ref == IssueRef(number=17, url="https://github.com/acme/repo/issues/17")
    assert len(provider.calls) == 1
    name, args = provider.calls[0]
    assert name == "create_issue"
    assert args["title"] == "loop-engine: 1 question(s) for run run-1"
    assert "1. **[ArchitecturePersona]** Which region?" in args["body"]
    assert args["label"] == "loop-engine/needs-human"
    assert args["repo"] is None


def test_mcp_issue_filer_forwards_explicit_repo() -> None:
    provider = _FakeProvider()
    filer = mcp_issue_filer(provider, repo="acme/repo")

    filer(_state(), _questions(), "state/run-1/01_awaiting_issue.json")

    assert provider.calls[0][1]["repo"] == "acme/repo"


def test_mcp_issue_reader_is_a_factory_matching_the_reader_seam() -> None:
    """R1: `mcp_issue_reader` returns a `Callable[[int], dict]`, the exact
    shape `cli`'s reader seam expects — not a raw 2-arg function."""
    provider = _FakeProvider()

    reader = mcp_issue_reader(provider)
    result = reader(17)

    assert result == {"state": "OPEN", "body": "b", "comments": []}
    assert provider.calls == [("read_issue", {"issue_number": 17, "repo": None})]


def test_mcp_issue_reader_forwards_explicit_repo() -> None:
    provider = _FakeProvider()
    reader = mcp_issue_reader(provider, repo="acme/repo")

    reader(17)

    assert provider.calls == [("read_issue", {"issue_number": 17, "repo": "acme/repo"})]


def test_default_issue_filer_opens_a_fresh_provider_per_call(monkeypatch) -> None:
    provider = _FakeProvider()
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.build_issue_provider", lambda: provider
    )
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.resolve_repo_slug", lambda cwd: "acme/repo"
    )

    ref = default_issue_filer(_state(), _questions(), "state/run-1/01_awaiting_issue.json")

    assert ref == IssueRef(number=17, url="https://github.com/acme/repo/issues/17")
    assert provider.calls[0][0] == "create_issue"


def test_default_issue_filer_names_the_origin_not_the_worktree_as_destination(
    monkeypatch, tmp_path
) -> None:
    """The R8 regression: by the time a stage escalates, the process CWD is the
    run's worktree, whose remote is loop-engine itself. The destination must be
    resolved against `origin_cwd()` — where the orchestrator was launched — and
    no caller should have to pass it."""
    provider = _FakeProvider()
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.build_issue_provider", lambda: provider
    )
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.resolve_repo_slug", lambda cwd: f"resolved{cwd}"
    )
    # Stand where a paused stage stands: inside the worktree, with the
    # orchestrator's origin recorded elsewhere.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.origin_cwd", lambda: Path("/orchestrator/checkout")
    )

    default_issue_filer(_state(), _questions(), "state/run-1/01.json")

    assert provider.calls[0][1]["repo"] == "resolved/orchestrator/checkout"


def test_default_issue_filer_cwd_override_wins_over_origin(monkeypatch) -> None:
    provider = _FakeProvider()
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.build_issue_provider", lambda: provider
    )
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.resolve_repo_slug", lambda cwd: f"resolved/{cwd}"
    )

    default_issue_filer(_state(), _questions(), "state/run-1/01.json", cwd="/orig")

    assert provider.calls[0][1]["repo"] == "resolved//orig"


def test_default_issue_reader_forwards_explicit_repo(monkeypatch) -> None:
    provider = _FakeProvider()
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.build_issue_provider", lambda: provider
    )

    default_issue_reader(17, repo="acme/managed")

    assert provider.calls == [("read_issue", {"issue_number": 17, "repo": "acme/managed"})]


def test_default_issue_reader_opens_a_fresh_provider_per_call(monkeypatch) -> None:
    provider = _FakeProvider()
    monkeypatch.setattr(
        "loop_engine.tools.issue_io.mcp_client.build_issue_provider", lambda: provider
    )

    result = default_issue_reader(17)

    assert result == {"state": "OPEN", "body": "b", "comments": []}
    assert provider.calls == [("read_issue", {"issue_number": 17, "repo": None})]
