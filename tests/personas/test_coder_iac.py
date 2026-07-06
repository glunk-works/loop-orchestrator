import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import State
from loop_engine.personas.coder_iac.persona import CoderIacPersona

TWO_SPRINTS = json.dumps(
    [
        {"path": "/sprints/01_foo/sprint_plan.md", "content": "Sprint one."},
        {"path": "/sprints/02_bar/sprint_plan.md", "content": "Sprint two."},
    ]
)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts=artifacts)


def test_coder_iac_persona_raises_key_error_when_sprint_plans_missing() -> None:
    mock_llm_client = MagicMock()

    with pytest.raises(KeyError):
        CoderIacPersona().run(_state({"architecture_definition": "# A"}), mock_llm_client)


def test_coder_iac_persona_runs_one_call_per_sprint_and_writes_reports() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.side_effect = [
        SimpleNamespace(text="Sprint 1 implemented."),
        SimpleNamespace(text="Sprint 2 implemented."),
    ]

    result_state = CoderIacPersona().run(
        _state({"architecture_definition": "# A", "sprint_plans": TWO_SPRINTS}),
        mock_llm_client,
    )

    assert mock_llm_client.call.call_count == 2
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert set(reports) == {"/sprints/01_foo/sprint_plan.md", "/sprints/02_bar/sprint_plan.md"}
    assert (Path("sprints") / "01_foo" / "implementation_report.md").exists()
    assert (Path("sprints") / "02_bar" / "implementation_report.md").exists()


def test_coder_iac_persona_stops_at_sprint_with_open_questions() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(
        text="Partial work.\n\n## Open Questions\n\n1. OIDC or API keys?"
    )

    result_state = CoderIacPersona().run(
        _state({"architecture_definition": "# A", "sprint_plans": TWO_SPRINTS}),
        mock_llm_client,
    )

    # Blocked on sprint 1: sprint 2 is not attempted until answers arrive.
    assert mock_llm_client.call.call_count == 1
    assert [q.text for q in result_state.questions] == ["OIDC or API keys?"]


def test_coder_iac_persona_skips_completed_sprints_on_reentry() -> None:
    prior_reports = json.dumps({"/sprints/01_foo/sprint_plan.md": "Done earlier."})
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text="Sprint 2 implemented.")

    result_state = CoderIacPersona().run(
        _state(
            {
                "architecture_definition": "# A",
                "sprint_plans": TWO_SPRINTS,
                "implementation_reports": prior_reports,
            }
        ),
        mock_llm_client,
    )

    assert mock_llm_client.call.call_count == 1
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert reports["/sprints/01_foo/sprint_plan.md"] == "Done earlier."
    assert reports["/sprints/02_bar/sprint_plan.md"] == "Sprint 2 implemented."
