"""Sprint Breakdown: declarative port is byte-parity incl. task_manifest."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import State
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.declarative.node import SprintBreakdownGenerator


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts=artifacts)


def _mock(text: str) -> MagicMock:
    m = MagicMock()
    m.call.return_value = SimpleNamespace(text=text)
    m.call_messages.return_value = SimpleNamespace(text=text)
    return m


ARCH = "# Architecture\n\nAll compute in eu-west-1."

RESP = """---

## GLOBAL DEFINITION OF DONE

- Tests pass.

---

### FILEPATH: /sprints/01_ci_cd_foundation/sprint_plan.md

**Sprint Goal:** Stand up CI.

**Dependencies:** None

**Tasks:**

- **Task 1: Add pipeline**
  - **Description:** Create the CI workflow.
  - **Target Files:** .github/workflows/ci.yml
  - **Acceptance Criteria:** CI runs on push.

---

### FILEPATH: /sprints/02_api_layer/sprint_plan.md

**Sprint Goal:** Build the API.

**Dependencies:** Sprint 1

**Tasks:**

- **Task 1: Add endpoint**
  - **Description:** Implement the health endpoint.
  - **Target Files:** src/api.py
  - **Acceptance Criteria:** GET /health returns 200.

---

## Open Questions

1. Which auth provider should the API use?
"""


def test_sprint_plans_and_manifest_byte_identical() -> None:
    classic = AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": ARCH}), _mock(RESP)
    )
    declarative = SprintBreakdownGenerator().run(
        _state({"architecture_definition": ARCH}), _mock(RESP)
    )

    assert declarative.artifacts["sprint_plans"] == classic.artifacts["sprint_plans"]
    assert declarative.artifacts["task_manifest"] == classic.artifacts["task_manifest"]


def test_open_questions_extracted_identically() -> None:
    classic = AgileSprintBreakdownPersona().run(
        _state({"architecture_definition": ARCH}), _mock(RESP)
    )
    declarative = SprintBreakdownGenerator().run(
        _state({"architecture_definition": ARCH}), _mock(RESP)
    )

    assert [q.text for q in declarative.questions] == [q.text for q in classic.questions]
    assert declarative.questions[0].text == "Which auth provider should the API use?"


def test_sprint_files_written(tmp_path) -> None:
    SprintBreakdownGenerator().run(_state({"architecture_definition": ARCH}), _mock(RESP))
    assert (tmp_path / "sprints/01_ci_cd_foundation/sprint_plan.md").is_file()
    assert (tmp_path / "sprints/02_api_layer/sprint_plan.md").is_file()


def test_section_merge_revision_parity() -> None:
    prior_blocks = (
        AgileSprintBreakdownPersona()
        .run(_state({"architecture_definition": ARCH}), _mock(RESP))
        .artifacts["sprint_plans"]
    )

    correction = (
        "### FILEPATH: /sprints/02_api_layer/sprint_plan.md\n\n"
        "**Sprint Goal:** Build the API with auth.\n\n"
        "**Dependencies:** Sprint 1\n\n"
        "**Tasks:**\n\n"
        "- **Task 1: Add endpoint**\n"
        "  - **Description:** Implement the health endpoint.\n"
        "  - **Target Files:** src/api.py\n"
        "  - **Acceptance Criteria:** GET /health returns 200.\n"
    )
    findings = ["Resolution: use OIDC"]
    base = {"architecture_definition": ARCH, "sprint_plans": prior_blocks}

    classic = AgileSprintBreakdownPersona().run(_state(base), _mock(correction), findings=findings)
    declarative = SprintBreakdownGenerator().run(_state(base), _mock(correction), findings=findings)
    assert declarative.artifacts["sprint_plans"] == classic.artifacts["sprint_plans"]
    assert declarative.artifacts["task_manifest"] == classic.artifacts["task_manifest"]


def test_consumes_produces_match() -> None:
    node = SprintBreakdownGenerator()
    assert node.consumes == ("architecture_definition",)
    assert node.produces == ("sprint_plans",)
