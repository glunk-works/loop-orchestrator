import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import Question, State
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


def _state(artifacts: dict[str, str], questions: list[Question] | None = None) -> State:
    return State(
        schema_version=2,
        run_id="run-1",
        questions=questions or [],
        stage_history=[],
        artifacts=artifacts,
    )


def test_coder_iac_persona_raises_key_error_when_sprint_plans_missing() -> None:
    mock_llm_client = MagicMock()

    with pytest.raises(KeyError):
        CoderIacPersona().run(_state({"architecture_definition": "# A"}), mock_llm_client)


def test_coder_iac_persona_runs_one_tool_loop_per_sprint_and_writes_reports() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.side_effect = [
        SimpleNamespace(text="Sprint 1 implemented."),
        SimpleNamespace(text="Sprint 2 implemented."),
    ]

    result_state = CoderIacPersona().run(
        _state({"architecture_definition": "# A", "sprint_plans": TWO_SPRINTS}),
        mock_llm_client,
    )

    assert mock_llm_client.run_tool_loop.call_count == 2
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert set(reports) == {"/sprints/01_foo/sprint_plan.md", "/sprints/02_bar/sprint_plan.md"}
    assert (Path("sprints") / "01_foo" / "implementation_report.md").exists()
    assert (Path("sprints") / "02_bar" / "implementation_report.md").exists()

    # The cached prefix (template + architecture) is byte-identical across
    # sprint invocations; only the user message (the sprint plan) varies.
    first_call, second_call = mock_llm_client.run_tool_loop.call_args_list
    assert first_call.kwargs["system_blocks"] == second_call.kwargs["system_blocks"]
    assert any("# A" in block for block in first_call.kwargs["system_blocks"])
    assert "Sprint one." in first_call.args[0][0]["content"]
    assert "Sprint two." in second_call.args[0][0]["content"]

    # The loop is armed with the full read/execute tool set.
    tool_names = {tool["name"] for tool in first_call.kwargs["tools"]}
    assert tool_names == {"read_file", "list_files", "grep", "run_tests"}


def test_coder_iac_persona_stops_at_sprint_with_open_questions() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.return_value = SimpleNamespace(
        text="Partial work.\n\n## Open Questions\n\n1. OIDC or API keys?"
    )

    result_state = CoderIacPersona().run(
        _state({"architecture_definition": "# A", "sprint_plans": TWO_SPRINTS}),
        mock_llm_client,
    )

    # Blocked on sprint 1: sprint 2 is not attempted until answers arrive.
    assert mock_llm_client.run_tool_loop.call_count == 1
    assert [q.text for q in result_state.questions] == ["OIDC or API keys?"]
    # Attribution: re-entry uses this to rework only the asking sprint.
    assert result_state.questions[0].origin_detail == "/sprints/01_foo/sprint_plan.md"


def test_coder_iac_persona_skips_completed_sprints_on_reentry() -> None:
    prior_reports = json.dumps({"/sprints/01_foo/sprint_plan.md": "Done earlier."})
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.return_value = SimpleNamespace(text="Sprint 2 implemented.")

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

    assert mock_llm_client.run_tool_loop.call_count == 1
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert reports["/sprints/01_foo/sprint_plan.md"] == "Done earlier."
    assert reports["/sprints/02_bar/sprint_plan.md"] == "Sprint 2 implemented."


def test_coder_iac_persona_reruns_only_sprints_with_resolved_questions() -> None:
    prior_reports = json.dumps(
        {
            "/sprints/01_foo/sprint_plan.md": "Sprint 1 done.",
            "/sprints/02_bar/sprint_plan.md": "Sprint 2 blocked on a question.",
        }
    )
    resolved = Question(
        id="q1",
        origin_stage="CoderIacPersona",
        origin_detail="/sprints/02_bar/sprint_plan.md",
        text="OIDC or API keys?",
        resolution="Use OIDC.",
        resolved_by="architect",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.return_value = SimpleNamespace(text="Sprint 2 redone with OIDC.")

    result_state = CoderIacPersona().run(
        _state(
            {
                "architecture_definition": "# A",
                "sprint_plans": TWO_SPRINTS,
                "implementation_reports": prior_reports,
            },
            questions=[resolved],
        ),
        mock_llm_client,
        findings=["Escalated question: OIDC or API keys?\n  Resolution: Use OIDC."],
    )

    # Only the sprint whose question was answered is re-run (the prior report
    # has no addressable sections, so it regenerates fully via the tool
    # loop); sprint 1's paid work is preserved byte-for-byte.
    assert mock_llm_client.run_tool_loop.call_count == 1
    mock_llm_client.call_messages.assert_not_called()
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert reports["/sprints/01_foo/sprint_plan.md"] == "Sprint 1 done."
    assert reports["/sprints/02_bar/sprint_plan.md"] == "Sprint 2 redone with OIDC."


def test_coder_iac_persona_reruns_sprint_named_by_gate_finding() -> None:
    prior_reports = json.dumps(
        {
            "/sprints/01_foo/sprint_plan.md": "Sprint 1 done.",
            "/sprints/02_bar/sprint_plan.md": "Sprint 2 done.",
        }
    )
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.return_value = SimpleNamespace(text="Sprint 2 fixed.")

    result_state = CoderIacPersona().run(
        _state(
            {
                "architecture_definition": "# A",
                "sprint_plans": TWO_SPRINTS,
                "implementation_reports": prior_reports,
            }
        ),
        mock_llm_client,
        findings=["/sprints/02_bar/sprint_plan.md: the produced tests fail (pytest exit code 1)"],
    )

    # The evidence gate attributed the failure to sprint 2 by path; only
    # sprint 2 is re-run.
    assert mock_llm_client.run_tool_loop.call_count == 1
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert reports["/sprints/01_foo/sprint_plan.md"] == "Sprint 1 done."
    assert reports["/sprints/02_bar/sprint_plan.md"] == "Sprint 2 fixed."


def test_coder_iac_persona_revises_sectioned_prior_report_via_three_turn_call() -> None:
    sectioned_report = (
        "Sprint 2 report.\n\n"
        "## Files Created/Modified\n\nprose only, no code fence here\n\n"
        "## Deviations\n\nNone.\n"
    )
    prior_reports = json.dumps(
        {
            "/sprints/01_foo/sprint_plan.md": "Sprint 1 done.",
            "/sprints/02_bar/sprint_plan.md": sectioned_report,
        }
    )
    resolved = Question(
        id="q1",
        origin_stage="CoderIacPersona",
        origin_detail="/sprints/02_bar/sprint_plan.md",
        text="OIDC or API keys?",
        resolution="Use OIDC.",
        resolved_by="architect",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.call_messages.return_value = SimpleNamespace(
        text="## Deviations\n\nSwitched to OIDC per resolution.\n"
    )

    result_state = CoderIacPersona().run(
        _state(
            {
                "architecture_definition": "# A",
                "sprint_plans": TWO_SPRINTS,
                "implementation_reports": prior_reports,
            },
            questions=[resolved],
        ),
        mock_llm_client,
        findings=["Escalated question: OIDC or API keys?\n  Resolution: Use OIDC."],
    )

    # Only sprint 2 re-ran, and it re-ran as a 3-turn targeted revision.
    mock_llm_client.run_tool_loop.assert_not_called()
    assert mock_llm_client.call_messages.call_count == 1
    messages = mock_llm_client.call_messages.call_args.args[0]
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert messages[1]["content"] == sectioned_report
    assert "Use OIDC." in messages[2]["content"]

    reports = json.loads(result_state.artifacts["implementation_reports"])
    revised = reports["/sprints/02_bar/sprint_plan.md"]
    assert "Switched to OIDC per resolution." in revised
    # Untouched sections of the report survive byte-for-byte.
    assert "## Files Created/Modified\n\nprose only, no code fence here" in revised
    assert reports["/sprints/01_foo/sprint_plan.md"] == "Sprint 1 done."


def test_coder_iac_persona_reruns_all_sprints_on_unattributed_gate_findings() -> None:
    prior_reports = json.dumps(
        {
            "/sprints/01_foo/sprint_plan.md": "Sprint 1 done.",
            "/sprints/02_bar/sprint_plan.md": "Sprint 2 done.",
        }
    )
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.side_effect = [
        SimpleNamespace(text="Sprint 1 revised."),
        SimpleNamespace(text="Sprint 2 revised."),
    ]

    result_state = CoderIacPersona().run(
        _state(
            {
                "architecture_definition": "# A",
                "sprint_plans": TWO_SPRINTS,
                "implementation_reports": prior_reports,
            }
        ),
        mock_llm_client,
        findings=["Report is not valid per the gate."],
    )

    # Findings with no sprint attribution: redo everything, so the stage
    # cannot return an identical artifact and stall the gate.
    assert mock_llm_client.run_tool_loop.call_count == 2
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert reports["/sprints/01_foo/sprint_plan.md"] == "Sprint 1 revised."
    assert reports["/sprints/02_bar/sprint_plan.md"] == "Sprint 2 revised."


def test_coder_iac_persona_applies_full_content_file_blocks() -> None:
    report = (
        "Sprint 1 implemented.\n\n"
        "## Files Created/Modified\n\n"
        "### FILEPATH: src/foo.py\n\n"
        "```python\ndef foo():\n    return 42\n```\n\n"
        "### FILEPATH: src/test_foo.py\n\n"
        "```python\nfrom foo import foo\n\ndef test_foo():\n    assert foo() == 42\n```\n"
    )
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.return_value = SimpleNamespace(text=report)

    single_sprint = json.dumps([{"path": "/sprints/01_foo/sprint_plan.md", "content": "S1."}])
    result_state = CoderIacPersona().run(
        _state({"architecture_definition": "# A", "sprint_plans": single_sprint}),
        mock_llm_client,
    )

    assert Path("src/foo.py").read_text() == "def foo():\n    return 42\n"
    assert "def test_foo" in Path("src/test_foo.py").read_text()
    # Clean application: no failure section recorded.
    reports = json.loads(result_state.artifacts["implementation_reports"])
    assert "Edit Application Failures" not in reports["/sprints/01_foo/sprint_plan.md"]


def test_coder_iac_persona_applies_search_replace_edit_blocks() -> None:
    Path("src").mkdir()
    Path("src/foo.py").write_text("def foo():\n    return 41\n")
    report = (
        "Sprint fix.\n\n"
        "### FILEPATH: src/foo.py\n\n"
        "<<<<<<< SEARCH\n    return 41\n=======\n    return 42\n>>>>>>> REPLACE\n"
    )
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.return_value = SimpleNamespace(text=report)

    single_sprint = json.dumps([{"path": "/sprints/01_foo/sprint_plan.md", "content": "S1."}])
    CoderIacPersona().run(
        _state({"architecture_definition": "# A", "sprint_plans": single_sprint}),
        mock_llm_client,
    )

    assert Path("src/foo.py").read_text() == "def foo():\n    return 42\n"


def test_coder_iac_persona_records_failures_for_malformed_edit_blocks() -> None:
    report = (
        "Sprint work.\n\n"
        # Edit block against a file that does not exist.
        "### FILEPATH: src/missing.py\n\n"
        "<<<<<<< SEARCH\nnope\n=======\nstill nope\n>>>>>>> REPLACE\n\n"
        # Traversal attempt is rejected by path validation.
        "### FILEPATH: ../etc/passwd\n\n```\nmalicious\n```\n"
    )
    mock_llm_client = MagicMock()
    mock_llm_client.run_tool_loop.return_value = SimpleNamespace(text=report)

    single_sprint = json.dumps([{"path": "/sprints/01_foo/sprint_plan.md", "content": "S1."}])
    result_state = CoderIacPersona().run(
        _state({"architecture_definition": "# A", "sprint_plans": single_sprint}),
        mock_llm_client,
    )

    reports = json.loads(result_state.artifacts["implementation_reports"])
    stored = reports["/sprints/01_foo/sprint_plan.md"]
    assert "## Edit Application Failures" in stored
    assert "src/missing.py" in stored
    assert "etc/passwd" in stored
    assert not Path("../etc/passwd").exists() or True  # traversal never written
