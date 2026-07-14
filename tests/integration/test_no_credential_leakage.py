import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from typer.testing import CliRunner

from loop_engine.cli import app
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS

runner = CliRunner()

FAKE_API_KEY = "sk-ant-test-SUPER-SECRET-FAKE-KEY-9f3a7c21"

# One sprint carrying exactly one manifest task: the Ralph Coder does one task
# per invocation, so a single-task manifest converges in a single increment (and
# therefore a single LLM call, which is what the canned transport below scripts).
SPRINT_BLOCKS_RESPONSE = """### FILEPATH: /sprints/01_foo/sprint_plan.md

**Sprint Goal:** Habit tracking.

**Tasks:**

- **Task 1: Add the habit placeholder test**
  - **Description:** Create the placeholder test module.
  - **Target Files:** `src/test_habit.py`
  - **Acceptance Criteria:** pytest is green.
"""


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


def test_completed_run_never_writes_the_api_key_to_disk(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("keyring.get_password", lambda *args: FAKE_API_KEY)

    # The Coder's response carries a file block producing a passing test:
    # the evidence gate re-runs pytest and only ACCEPTs a green tree.
    coder_response = (
        "Sprint 1 implemented.\n\n"
        "## Files Created/Modified\n\n"
        "### FILEPATH: src/test_habit.py\n\n"
        "```python\ndef test_habit_placeholder():\n    assert True\n```\n"
    )
    mock_transport = MagicMock()
    mock_transport.messages.create.side_effect = [
        _response(10, 10, json.dumps(_clean_pm_answers())),  # PM
        _response(10, 10, "# Architecture Definition\n..."),  # Architecture
        _response(10, 10, SPRINT_BLOCKS_RESPONSE),  # Agile Sprint Breakdown
        _response(10, 10, coder_response),  # Coder/IaC (end_turn: 1 loop call)
    ]
    monkeypatch.setattr("anthropic.Anthropic", lambda **kwargs: mock_transport)

    input_path = tmp_path / "input.md"
    input_path.write_text("We need a habit tracker for busy parents.")

    result = runner.invoke(app, ["run", "--input", str(input_path), "--budget", "100.0"])

    assert result.exit_code == 0

    state_dir = tmp_path / "state"
    snapshot_files = list(state_dir.rglob("*.json"))
    # Four accepted-stage snapshots plus the terminal completed snapshot.
    assert len(snapshot_files) == 5

    for snapshot_path in snapshot_files:
        content = snapshot_path.read_text()
        assert FAKE_API_KEY not in content

    # The API key must not leak into produced artifacts either.
    for artifact_path in (tmp_path / "sprints").rglob("*.md"):
        assert FAKE_API_KEY not in artifact_path.read_text()
