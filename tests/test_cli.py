import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import typer
from typer.testing import CliRunner

from loop_engine.cli import ABORTED_BY_HUMAN_EXIT_CODE, app
from loop_engine.core.state import (
    CURRENT_SCHEMA_VERSION,
    IssueRef,
    Question,
    RunStatus,
    State,
)
from loop_engine.loops.default.loop import DEFAULT_LOOP

runner = CliRunner()

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _plain_output(result) -> str:
    # Rich (Typer's help renderer) force-enables ANSI styling in CI
    # (it detects the GITHUB_ACTIONS env var), but not in a local shell
    # piping to a StringIO — strip escape codes so assertions are
    # environment-independent either way.
    return _ANSI_ESCAPE_RE.sub("", result.output)


def _completed_state(**overrides) -> State:
    defaults = dict(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.COMPLETED,
        stage_history=[],
        artifacts={},
    )
    return State(**{**defaults, **overrides})


def test_cli_help_exits_zero_and_lists_run_and_resume_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = _plain_output(result)
    assert "run" in output
    assert "resume" in output


def test_cli_run_help_lists_expected_options() -> None:
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    output = _plain_output(result)
    for option in ("--loop", "--input", "--budget", "--resume-from"):
        assert option in output


def test_cli_run_always_drives_the_langgraph_engine(tmp_path, monkeypatch) -> None:
    # The fresh-run path delegates to `runner.run_new`, so the engine reference
    # patched here lives on `loop_engine.runner`, not `cli`. Phase 6: the engine
    # is unconditional — no flag, no classic driver to fall back to.
    mock_graph = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.runner.run_graph_loop", mock_graph)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    result = runner.invoke(app, ["run"])

    assert result.exit_code == 0
    assert mock_graph.called


def test_cli_resume_from_skips_already_completed_stages(tmp_path, monkeypatch) -> None:
    fixture_state = State(
        schema_version=2,
        run_id="run-1",
        stage_history=[
            {
                "stage_name": "PMGenerator",
                "tokens_used": 10,
                "cost_usd": 0.0,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        ],
        artifacts={"project_spec": '{"problem_statement": "x"}'},
    )
    state_path = tmp_path / "state.json"
    state_path.write_text(fixture_state.model_dump_json())

    mock_run_graph_loop = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.cli.run_graph_loop", mock_run_graph_loop)
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())

    result = runner.invoke(app, ["run", "--resume-from", str(state_path)])

    assert result.exit_code == 0
    assert mock_run_graph_loop.call_args.kwargs["start_index"] == 1


def test_cli_resume_from_migrates_v1_snapshot(tmp_path, monkeypatch) -> None:
    v1_payload = {
        "schema_version": 1,
        "run_id": "run-legacy",
        "stage_history": [
            {
                "stage_name": "PMGenerator",
                "tokens_used": 10,
                "cost_usd": 0.0,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        ],
        "artifacts": {"project_spec": "{}"},
    }
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(v1_payload))

    mock_run_graph_loop = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.cli.run_graph_loop", mock_run_graph_loop)
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())

    result = runner.invoke(app, ["run", "--resume-from", str(state_path)])

    assert result.exit_code == 0
    resumed_state = mock_run_graph_loop.call_args.args[1]
    assert resumed_state.schema_version == CURRENT_SCHEMA_VERSION


def test_cli_resume_from_rejects_snapshot_from_a_different_loop(tmp_path, monkeypatch) -> None:
    foreign_state = State(
        schema_version=2,
        run_id="run-1",
        stage_history=[
            {
                "stage_name": "SomeOtherPersona",
                "tokens_used": 10,
                "cost_usd": 0.0,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        ],
        artifacts={},
    )
    state_path = tmp_path / "state.json"
    state_path.write_text(foreign_state.model_dump_json())
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())

    result = runner.invoke(app, ["run", "--resume-from", str(state_path)])

    assert result.exit_code != 0
    assert "SomeOtherPersona" in _plain_output(result)


def test_cli_resume_from_issue_folds_answers_and_reenters(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("loop_engine.cli.resolve_repo_slug", lambda cwd: "acme/repo")
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=17, url="https://github.com/acme/repo/issues/17"),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitectureGenerator", text="Which region?")],
        stage_history=[
            {
                "stage_name": "PMGenerator",
                "tokens_used": 10,
                "cost_usd": 0.0,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        ],
        artifacts={"project_spec": "{}"},
    )
    snapshot_path = tmp_path / "01_awaiting_issue.json"
    snapshot_path.write_text(paused.model_dump_json())

    monkeypatch.setattr(
        "loop_engine.cli.default_issue_reader",
        lambda n, repo=None: {
            "state": "OPEN",
            "url": "https://github.com/acme/repo/issues/17",
            "body": f"Snapshot: `{snapshot_path}`",
            "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
        },
    )
    mock_run_graph_loop = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.cli.run_graph_loop", mock_run_graph_loop)
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())

    fold_result_holder = {}

    def fake_fold(self, state, llm_client):
        fold_result_holder["questions"] = state.questions
        return state

    monkeypatch.setattr(type(DEFAULT_LOOP.stages[0].persona), "fold_answers", fake_fold)

    result = runner.invoke(app, ["resume", "--from-issue", "17"])

    assert result.exit_code == 0
    # The human's answer was applied before folding.
    assert fold_result_holder["questions"][0].resolution == "eu-west-1"
    assert fold_result_holder["questions"][0].resolved_by == "human:17"
    # Resumes at the paused stage (no impact classified → default in fold).
    assert mock_run_graph_loop.call_args.kwargs["start_index"] == 1
    assert any("eu-west-1" in f for f in mock_run_graph_loop.call_args.kwargs["initial_findings"])
    # R2/R8: a re-escalation from the resumed run writes through the same route.
    # The CLI deliberately injects NO `issue_filer` — `default_issue_filer`
    # resolves its own destination from `worktree.origin_cwd()`, so every
    # entrypoint is correct rather than only the ones that remembered to thread a
    # cwd (which is exactly how the fresh-run paths kept leaking).
    assert "issue_filer" not in mock_run_graph_loop.call_args.kwargs


def test_cli_resume_from_issue_dispatches_the_real_default_through_mcp(
    tmp_path, monkeypatch
) -> None:
    """The runtime default reader is genuinely MCP-backed: with no cli-level
    monkeypatching of `default_issue_reader` itself, only a fake provider
    swapped in under `build_issue_provider` (no real gh/subprocess), `resume
    --from-issue` still resolves questions correctly end to end."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("loop_engine.cli.resolve_repo_slug", lambda cwd: "acme/repo")
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=17, url="https://github.com/acme/repo/issues/17"),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitectureGenerator", text="Which region?")],
        stage_history=[
            {
                "stage_name": "PMGenerator",
                "tokens_used": 10,
                "cost_usd": 0.0,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        ],
        artifacts={"project_spec": "{}"},
    )
    snapshot_path = tmp_path / "01_awaiting_issue.json"
    snapshot_path.write_text(paused.model_dump_json())

    class _FakeProvider:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return None

        def execute(self, name: str, arguments: dict) -> str:
            assert name == "read_issue"
            assert arguments == {"issue_number": 17, "repo": "acme/repo"}
            return json.dumps(
                {
                    "state": "OPEN",
                    "url": "https://github.com/acme/repo/issues/17",
                    "body": f"Snapshot: `{snapshot_path}`",
                    "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
                }
            )

    monkeypatch.setattr("loop_engine.tools.mcp.build_issue_provider", lambda: _FakeProvider())
    mock_run_graph_loop = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.cli.run_graph_loop", mock_run_graph_loop)
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())

    fold_result_holder = {}

    def fake_fold(self, state, llm_client):
        fold_result_holder["questions"] = state.questions
        return state

    monkeypatch.setattr(type(DEFAULT_LOOP.stages[0].persona), "fold_answers", fake_fold)

    result = runner.invoke(app, ["resume", "--from-issue", "17"])

    assert result.exit_code == 0
    assert fold_result_holder["questions"][0].resolution == "eu-west-1"
    assert fold_result_holder["questions"][0].resolved_by == "human:17"
    assert "Reading issue #17 from acme/repo" in _plain_output(result)


def test_cli_resume_from_issue_aborts_cleanly_when_closed_without_answers(
    tmp_path, monkeypatch
) -> None:
    """R5: closing the issue without an answers comment is a documented,
    clean abort — not an uncaught traceback."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("loop_engine.cli.resolve_repo_slug", lambda cwd: "acme/repo")
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=17, url="https://github.com/acme/repo/issues/17"),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitectureGenerator", text="Which region?")],
        stage_history=[],
        artifacts={"project_spec": "{}"},
    )
    snapshot_path = tmp_path / "01_awaiting_issue.json"
    snapshot_path.write_text(paused.model_dump_json())

    monkeypatch.setattr(
        "loop_engine.cli.default_issue_reader",
        lambda n, repo=None: {
            "state": "CLOSED",
            "url": "https://github.com/acme/repo/issues/17",
            "body": f"Snapshot: `{snapshot_path}`",
            "comments": [{"body": "won't fix"}],
        },
    )
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())

    result = runner.invoke(app, ["resume", "--from-issue", "17"])

    assert result.exit_code == ABORTED_BY_HUMAN_EXIT_CODE
    assert result.exit_code != 1, "a deliberate human abort must be distinguishable from a crash"
    assert "#17" in _plain_output(result)
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_cli_resume_from_issue_folds_answers_via_the_pm_generator(tmp_path, monkeypatch) -> None:
    # Regression for review finding #1: stage 0 is PMGenerator, which must expose
    # fold_answers or every paused run is unresumable (cli.py's resume guard
    # raises typer.BadParameter).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("loop_engine.cli.resolve_repo_slug", lambda cwd: "acme/repo")
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=17, url="https://github.com/acme/repo/issues/17"),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitectureGenerator", text="Which region?")],
        stage_history=[
            {
                "stage_name": "PMGenerator",
                "tokens_used": 10,
                "cost_usd": 0.0,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        ],
        artifacts={"project_spec": "{}"},
    )
    snapshot_path = tmp_path / "01_awaiting_issue.json"
    snapshot_path.write_text(paused.model_dump_json())

    monkeypatch.setattr(
        "loop_engine.cli.default_issue_reader",
        lambda n, repo=None: {
            "state": "OPEN",
            "url": "https://github.com/acme/repo/issues/17",
            "body": f"Snapshot: `{snapshot_path}`",
            "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
        },
    )
    monkeypatch.setattr(
        "loop_engine.cli.run_graph_loop", MagicMock(return_value=_completed_state())
    )
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text='{"spec_updates": {}, "impacts": {}}')
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock(return_value=mock_llm_client))

    result = runner.invoke(app, ["resume", "--from-issue", "17"])

    assert result.exit_code == 0


def test_cli_cost_summary_counts_each_stage_once_despite_terminal_snapshot(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "state" / "run-1"
    run_dir.mkdir(parents=True)

    stage_names = ["PMGenerator", "ArchitectureGenerator"]
    tokens = [20, 80]
    history = []
    for index, (name, t) in enumerate(zip(stage_names, tokens, strict=True)):
        history.append(
            {
                "stage_name": name,
                "tokens_used": t,
                "cost_usd": 0.0,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        )
        state = State(
            schema_version=2,
            run_id="run-1",
            stage_history=list(history),
            artifacts={},
        )
        (run_dir / f"{index:02d}_{name}.json").write_text(state.model_dump_json())

    # Terminal snapshot duplicates the final history — the old implementation
    # double-counted the last stage because of files like this.
    terminal = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.BUDGET_EXCEEDED,
        stage_history=list(history),
        artifacts={},
    )
    (run_dir / "02_budget_exceeded.json").write_text(terminal.model_dump_json())

    result = runner.invoke(app, ["cost-summary", "--run-id", "run-1"])

    assert result.exit_code == 0
    output = _plain_output(result)
    assert str(sum(tokens)) in output
    assert str(sum(tokens) + tokens[-1]) not in output
    # Cache activity and real dollars are part of the summary.
    assert "Cache W" in output
    assert "Cache R" in output
    assert "Cost (USD)" in output


def _init_repo(path: Path) -> None:
    for args in (
        ["init", "-b", "main"],
        ["config", "user.email", "t@t.test"],
        ["config", "user.name", "T"],
    ):
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)
    (path / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "seed.txt"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=path, check=True, capture_output=True)


def test_cli_run_under_worktree_isolation_runs_engine_in_worktree(tmp_path, monkeypatch) -> None:
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "worktree")

    seen = {}

    def fake_run_graph_loop(loop, state, client, **kwargs):
        seen["cwd"] = Path.cwd()
        return _completed_state()

    monkeypatch.setattr("loop_engine.runner.run_graph_loop", fake_run_graph_loop)
    monkeypatch.setattr("loop_engine.runner.LLMClient", MagicMock())

    origin = Path.cwd()
    result = runner.invoke(app, ["run"])

    assert result.exit_code == 0
    # The engine ran inside a per-run worktree, not the main checkout...
    assert seen["cwd"] != origin
    assert (tmp_path / ".worktrees").resolve() == seen["cwd"].parent
    # ...and the CWD was restored afterward.
    assert Path.cwd() == origin


def test_cli_prune_worktrees_all_removes_worktrees(tmp_path, monkeypatch) -> None:
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "worktree")

    from loop_engine.tools.worktree import create

    create("runa")
    create("runb")

    result = runner.invoke(app, ["prune-worktrees", "--all"])

    assert result.exit_code == 0
    assert not (tmp_path / ".worktrees" / "runa").exists()
    assert not (tmp_path / ".worktrees" / "runb").exists()


def test_cli_prune_worktrees_requires_a_target(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["prune-worktrees"])
    assert result.exit_code != 0


def test_cli_defines_no_api_key_option() -> None:
    click_app = typer.main.get_command(app)
    for command in click_app.commands.values():
        for param in command.params:
            assert "api_key" not in (param.name or "")
            assert not any("api-key" in opt.lower() for opt in getattr(param, "opts", []))


def _paused_on_issue(tmp_path, *, number=17, url="https://github.com/acme/managed/issues/17"):
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=number, url=url),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitectureGenerator", text="Which region?")],
        stage_history=[],
        artifacts={"project_spec": "{}"},
    )
    snapshot_path = tmp_path / "01_awaiting_issue.json"
    snapshot_path.write_text(paused.model_dump_json())
    return snapshot_path


def test_cli_resume_from_issue_silently_resumes_a_same_numbered_wrong_repo_issue(
    tmp_path, monkeypatch
) -> None:
    """F1/F2 reframe: there is no inconsistent state left for the code to
    detect here. loop-engine's own #17 is a REAL, unrelated escalation issue
    -- filed by some earlier loop-engine-scoped run -- carrying its own
    Snapshot: line and its own pending_issue.number == 17. Resuming
    `--from-issue 17` from the loop-engine checkout (no --repo) reads that
    genuine issue, loads that genuine (wrong) run, and every check --
    including the F1c integrity check -- passes, because both sides
    legitimately agree (they were read out of the very same issue). This
    test documents the residual ambiguity rather than pretending a downstream
    comparison closes it: the echoed destination (F1b) is the only actual
    defense, and it is on the human to read it.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("loop_engine.cli.resolve_repo_slug", lambda cwd: "glunk-works/loop-engine")

    # loop-engine's OWN local paused run, genuinely paused on loop-engine's
    # own issue #17 -- unrelated to the managed run the human actually meant.
    wrong_run_snapshot = _paused_on_issue(
        tmp_path, number=17, url="https://github.com/glunk-works/loop-engine/issues/17"
    )

    monkeypatch.setattr(
        "loop_engine.cli.default_issue_reader",
        lambda n, repo=None: {
            "state": "OPEN",
            "url": "https://github.com/glunk-works/loop-engine/issues/17",
            "body": f"Snapshot: `{wrong_run_snapshot}`",
            "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
        },
    )
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())
    mock_graph = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.cli.run_graph_loop", mock_graph)
    monkeypatch.setattr(
        type(DEFAULT_LOOP.stages[0].persona), "fold_answers", lambda self, state, llm: state
    )

    result = runner.invoke(app, ["resume", "--from-issue", "17"])

    # The code proceeds -- it genuinely cannot tell this apart from a correct
    # resume, since both sides of every check agree by construction.
    assert result.exit_code == 0
    assert mock_graph.called
    # The echoed destination is the human's only signal that this is the
    # wrong repo (a real `glunk-works/loop-engine` checkout, not the managed
    # repo the escalation was actually meant for).
    assert "Reading issue #17 from glunk-works/loop-engine" in _plain_output(result)


def test_cli_resume_snapshot_derives_repo_and_issue_from_pending_issue_not_cwd(
    tmp_path, monkeypatch
) -> None:
    """F1a: --snapshot is the unambiguous path -- repo and issue number come
    from the snapshot's own pending_issue.url; CWD is never consulted."""
    monkeypatch.chdir(tmp_path)
    snapshot_path = _paused_on_issue(
        tmp_path, number=17, url="https://github.com/acme/managed/issues/17"
    )

    def _must_not_be_called(cwd):
        raise AssertionError("resolve_repo_slug must not run when --snapshot is given")

    monkeypatch.setattr("loop_engine.cli.resolve_repo_slug", _must_not_be_called)

    seen = {}

    def fake_reader(n, repo=None):
        seen["number"] = n
        seen["repo"] = repo
        return {
            "state": "OPEN",
            "url": "https://github.com/acme/managed/issues/17",
            "body": f"Snapshot: `{snapshot_path}`",
            "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
        }

    monkeypatch.setattr("loop_engine.cli.default_issue_reader", fake_reader)
    monkeypatch.setattr(
        "loop_engine.cli.run_graph_loop", MagicMock(return_value=_completed_state())
    )
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())
    monkeypatch.setattr(
        type(DEFAULT_LOOP.stages[0].persona), "fold_answers", lambda self, state, llm: state
    )

    result = runner.invoke(app, ["resume", "--snapshot", str(snapshot_path)])

    assert result.exit_code == 0
    assert seen["number"] == 17
    assert seen["repo"] == "acme/managed"


def test_cli_resume_requires_from_issue_or_snapshot(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["resume"])
    assert result.exit_code != 0
    assert "--snapshot" in _plain_output(result)


def test_cli_resume_raises_on_missing_issue_url(tmp_path, monkeypatch) -> None:
    """F5: read_issue always requests `url`; a missing one signals something
    already went wrong and must raise, not silently skip the integrity check."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("loop_engine.cli.resolve_repo_slug", lambda cwd: "acme/repo")
    snapshot_path = _paused_on_issue(tmp_path, url="https://github.com/acme/repo/issues/17")

    monkeypatch.setattr(
        "loop_engine.cli.default_issue_reader",
        lambda n, repo=None: {
            "state": "OPEN",
            "body": f"Snapshot: `{snapshot_path}`",
            "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
        },
    )
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())
    mock_graph = MagicMock(return_value=_completed_state())
    monkeypatch.setattr("loop_engine.cli.run_graph_loop", mock_graph)

    result = runner.invoke(app, ["resume", "--from-issue", "17"])

    assert result.exit_code != 0
    assert not mock_graph.called


def test_cli_resume_passes_repo_through_to_the_reader(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    snapshot_path = _paused_on_issue(tmp_path)
    seen = {}

    def fake_reader(n, repo=None):
        seen["repo"] = repo
        return {
            "state": "OPEN",
            "url": "https://github.com/acme/managed/issues/17",
            "body": f"Snapshot: `{snapshot_path}`",
            "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
        }

    monkeypatch.setattr("loop_engine.cli.default_issue_reader", fake_reader)
    monkeypatch.setattr(
        "loop_engine.cli.run_graph_loop", MagicMock(return_value=_completed_state())
    )
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())
    monkeypatch.setattr(
        type(DEFAULT_LOOP.stages[0].persona), "fold_answers", lambda self, state, llm: state
    )

    result = runner.invoke(app, ["resume", "--from-issue", "17", "--repo", "acme/managed"])

    assert result.exit_code == 0
    assert seen["repo"] == "acme/managed"
