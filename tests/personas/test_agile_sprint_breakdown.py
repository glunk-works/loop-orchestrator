import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import State
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona

TWO_SPRINT_RESPONSE = """### FILEPATH: /sprints/01_foo/sprint_plan.md

Sprint one content.

---

### FILEPATH: /sprints/02_bar/sprint_plan.md

Sprint two content.
"""


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts=artifacts)


def test_agile_sprint_breakdown_persona_raises_key_error_when_architecture_missing() -> None:
    mock_llm_client = MagicMock()

    with pytest.raises(KeyError):
        AgileSprintBreakdownPersona().run(_state({}), mock_llm_client)


def test_agile_sprint_breakdown_persona_parses_two_sprint_blocks() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text=TWO_SPRINT_RESPONSE)

    result_state = AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": "# Architecture\n..."}), mock_llm_client
    )

    sprint_plans = json.loads(result_state.artifacts["sprint_plans"])
    assert len(sprint_plans) == 2
    assert sprint_plans[0]["path"] == "/sprints/01_foo/sprint_plan.md"
    assert "Sprint one content." in sprint_plans[0]["content"]
    assert sprint_plans[1]["path"] == "/sprints/02_bar/sprint_plan.md"
    assert "Sprint two content." in sprint_plans[1]["content"]


def test_agile_sprint_breakdown_persona_puts_template_and_architecture_in_system_blocks() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text=TWO_SPRINT_RESPONSE)

    AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": "# Architecture\n..."}), mock_llm_client
    )

    system_blocks = mock_llm_client.call.call_args.kwargs["system_blocks"]
    assert any("Agile Project Manager" in block for block in system_blocks)
    assert any("# Architecture\n..." in block for block in system_blocks)
    assert "# Architecture" not in mock_llm_client.call.call_args.args[0]


def test_agile_sprint_breakdown_persona_writes_sprint_plan_files() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text=TWO_SPRINT_RESPONSE)

    AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": "# Architecture\n..."}), mock_llm_client
    )

    assert (Path("sprints") / "01_foo" / "sprint_plan.md").read_text() == "Sprint one content."
    assert (Path("sprints") / "02_bar" / "sprint_plan.md").read_text() == "Sprint two content."


def test_agile_sprint_breakdown_persona_skips_invalid_paths_without_crashing() -> None:
    response = (
        "### FILEPATH: /etc/passwd\n\nmalicious\n\n"
        "### FILEPATH: /sprints/01_ok/sprint_plan.md\n\ngood"
    )
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text=response)

    result_state = AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": "# Architecture"}), mock_llm_client
    )

    assert not Path("/etc/passwd_written_by_test").exists()
    assert (Path("sprints") / "01_ok" / "sprint_plan.md").exists()
    # Both blocks stay in state (auditability); only valid paths hit disk.
    assert len(json.loads(result_state.artifacts["sprint_plans"])) == 2


def test_agile_sprint_breakdown_persona_revises_only_flagged_sprint_files() -> None:
    prior_blocks = json.dumps(
        [
            {"path": "/sprints/01_foo/sprint_plan.md", "content": "Sprint one content."},
            {"path": "/sprints/02_bar/sprint_plan.md", "content": "Sprint two content."},
        ]
    )
    mock_llm_client = MagicMock()
    mock_llm_client.call_messages.return_value = SimpleNamespace(
        text="### FILEPATH: /sprints/02_bar/sprint_plan.md\n\nSprint two, corrected.\n"
    )

    result_state = AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": "# Architecture", "sprint_plans": prior_blocks}),
        mock_llm_client,
        findings=["Sprint two lacks a security task."],
    )

    mock_llm_client.call.assert_not_called()
    messages = mock_llm_client.call_messages.call_args.args[0]
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert "Sprint one content." in messages[1]["content"]
    assert "Sprint two lacks a security task." in messages[2]["content"]

    plans = {b["path"]: b["content"] for b in json.loads(result_state.artifacts["sprint_plans"])}
    # Untouched sprint byte-identical; flagged sprint replaced.
    assert plans["/sprints/01_foo/sprint_plan.md"] == "Sprint one content."
    assert plans["/sprints/02_bar/sprint_plan.md"] == "Sprint two, corrected."


def test_agile_sprint_breakdown_persona_captures_open_questions() -> None:
    response = TWO_SPRINT_RESPONSE + "\n## Open Questions\n\n1. Which CI provider?\n"
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text=response)

    result_state = AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": "# Architecture"}), mock_llm_client
    )

    assert [q.text for q in result_state.questions] == ["Which CI provider?"]
    assert result_state.questions[0].origin_stage == "AgileSprintBreakdownPersona"
