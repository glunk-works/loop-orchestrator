import re
from unittest.mock import MagicMock

import typer
from typer.testing import CliRunner

from loop_engine.cli import app
from loop_engine.core.state import State
from loop_engine.loops.default.loop import DEFAULT_LOOP

runner = CliRunner()

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _plain_output(result) -> str:
    # Rich (Typer's help renderer) force-enables ANSI styling in CI
    # (it detects the GITHUB_ACTIONS env var), but not in a local shell
    # piping to a StringIO — strip escape codes so assertions are
    # environment-independent either way.
    return _ANSI_ESCAPE_RE.sub("", result.output)


def test_cli_help_exits_zero_and_lists_run_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "run" in _plain_output(result)


def test_cli_run_help_lists_expected_options() -> None:
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    output = _plain_output(result)
    for option in ("--loop", "--input", "--budget", "--resume-from"):
        assert option in output


def test_cli_resume_from_skips_already_completed_stages(tmp_path, monkeypatch) -> None:
    fixture_state = State(
        schema_version=1,
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

    mock_run_loop = MagicMock(return_value=fixture_state)
    monkeypatch.setattr("loop_engine.cli.run_loop", mock_run_loop)
    monkeypatch.setattr("loop_engine.cli.LLMClient", MagicMock())

    result = runner.invoke(app, ["run", "--resume-from", str(state_path)])

    assert result.exit_code == 0
    called_loop = mock_run_loop.call_args.args[0]
    assert called_loop == DEFAULT_LOOP[1:]


def test_cli_defines_no_api_key_option() -> None:
    click_app = typer.main.get_command(app)
    run_command = click_app.commands["run"]

    for param in run_command.params:
        assert "api_key" not in (param.name or "")
        assert not any("api-key" in opt.lower() for opt in getattr(param, "opts", []))
