import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from typer.testing import CliRunner

from loop_engine.cli import app
from loop_engine.core.state import RunStatus, State
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS

runner = CliRunner()


def _response(input_tokens: int, output_tokens: int, text: str) -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        content=[SimpleNamespace(text=text)],
        stop_reason="end_turn",
    )


def _clean_pm_answers() -> dict[str, str]:
    answers = {field: f"Answer for {field}." for field in CHECKLIST_FIELDS}
    answers["acceptance_criteria"] = "A user can create, complete, and delete a habit."
    answers["out_of_scope"] = "Multi-tenant billing and mobile apps."
    return answers


def test_budget_abort_persists_completed_snapshots_and_terminal_status(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("keyring.get_password", lambda *args: "fake-api-key")

    # Each real call's own pre-flight estimate is ~len(prompt)/4 + max_tokens,
    # so the budget must clear both calls' estimates while the *actual*
    # mocked usage below still exhausts the budget before stage 3 is invoked.
    mock_transport = MagicMock()
    mock_transport.messages.create.side_effect = [
        _response(20_000, 20_000, json.dumps(_clean_pm_answers())),  # PM: stage 1
        _response(20_000, 20_000, "# Architecture Definition\n..."),  # Arch: stage 2
    ]
    monkeypatch.setattr("anthropic.Anthropic", lambda **kwargs: mock_transport)

    input_path = tmp_path / "input.md"
    input_path.write_text("We need a habit tracker for busy parents.")

    result = runner.invoke(app, ["run", "--input", str(input_path), "--budget", "80000"])

    # Budget exhaustion is an orderly pause, not a crash: dedicated exit code.
    assert result.exit_code == 3

    # Only PM and Architecture's transport calls were ever made; the engine's
    # budget check stops the run before the third stage is invoked.
    assert mock_transport.messages.create.call_count == 2

    run_dirs = list((tmp_path / "state").iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    pm_snapshot = State.model_validate_json((run_dir / "00_PMPersona.json").read_text())
    assert pm_snapshot.stage_history[-1].stage_name == "PMPersona"

    architecture_snapshot = State.model_validate_json(
        (run_dir / "01_ArchitecturePersona.json").read_text()
    )
    assert architecture_snapshot.stage_history[-1].stage_name == "ArchitecturePersona"

    # And a terminal snapshot records WHY the run stopped.
    terminal = State.model_validate_json((run_dir / "02_budget_exceeded.json").read_text())
    assert terminal.status is RunStatus.BUDGET_EXCEEDED
