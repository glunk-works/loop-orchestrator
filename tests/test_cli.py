import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import typer
from typer.testing import CliRunner

from loop_engine.cli import app
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
                "stage_name": "PMPersona",
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
                "stage_name": "PMPersona",
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
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=17, url="https://github.com/acme/repo/issues/17"),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitecturePersona", text="Which region?")],
        stage_history=[
            {
                "stage_name": "PMPersona",
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
        "loop_engine.cli.issue_io.read_issue",
        lambda n: {
            "state": "OPEN",
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


def test_cli_resume_from_issue_via_injected_mcp_reader(tmp_path, monkeypatch) -> None:
    """Read-side seam: with an MCP-backed reader injected (a fake provider,
    no real gh/subprocess), `resume --from-issue` resolves questions
    identically to the classic path. Default stays classic; this only proves
    the injection wiring works end to end."""
    from loop_engine.tools.issue_io import mcp_read_issue

    monkeypatch.chdir(tmp_path)
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=17, url="https://github.com/acme/repo/issues/17"),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitecturePersona", text="Which region?")],
        stage_history=[
            {
                "stage_name": "PMPersona",
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
        def execute(self, name: str, arguments: dict) -> str:
            assert name == "read_issue"
            assert arguments == {"issue_number": 17}
            return json.dumps(
                {
                    "state": "OPEN",
                    "body": f"Snapshot: `{snapshot_path}`",
                    "comments": [{"body": "```answers\n1: eu-west-1\n```"}],
                }
            )

    monkeypatch.setattr(
        "loop_engine.cli._issue_reader",
        lambda n: mcp_read_issue(_FakeProvider(), n),
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
    assert fold_result_holder["questions"][0].resolution == "eu-west-1"
    assert fold_result_holder["questions"][0].resolved_by == "human:17"


def test_cli_resume_from_issue_works_under_declarative_personas(tmp_path, monkeypatch) -> None:
    # Regression for review finding #1: under `declarative`, stage 0 is
    # PMGenerator, which must expose fold_answers or every paused declarative
    # run is unresumable (cli.py's resume guard raises typer.BadParameter).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOOP_ENGINE_PERSONAS", "declarative")
    paused = State(
        schema_version=2,
        run_id="run-1",
        status=RunStatus.AWAITING_ISSUE,
        pending_issue=IssueRef(number=17, url="https://github.com/acme/repo/issues/17"),
        counters={"paused_stage_index": 1},
        questions=[Question(id="q1", origin_stage="ArchitecturePersona", text="Which region?")],
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
        "loop_engine.cli.issue_io.read_issue",
        lambda n: {
            "state": "OPEN",
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

    stage_names = ["PMPersona", "ArchitecturePersona"]
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
