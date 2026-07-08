"""Cross-engine parity for the declarative document personas: a PM → Architect
→ Sprint Breakdown pipeline drives identically under run_loop and the LangGraph
engine, reaching the same artifacts on the happy path."""

import json
from types import SimpleNamespace

import pytest

from loop_engine.core.engine import Loop, Stage, run_loop
from loop_engine.core.gates import ArtifactGate
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import IssueRef, RunStatus, State
from loop_engine.personas.declarative.node import (
    ArchitectureGenerator,
    PMGenerator,
    SprintBreakdownGenerator,
)
from loop_engine.personas.pm.critic_gate import CriticGate
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _stub_issue_filer(monkeypatch):
    def fake_file_issue(state, questions, snapshot_path):
        return IssueRef(number=1, url="https://example/1")

    monkeypatch.setattr("loop_engine.core.engine.file_question_issue", fake_file_issue)


_CLEAN = {field: f"value for {field}" for field in CHECKLIST_FIELDS}
_CLEAN["in_scope"] = "reset flow"
_CLEAN["out_of_scope"] = "sso"
_CLEAN["acceptance_criteria"] = "A user resets their password end to end within five minutes."

PM_JSON = json.dumps(_CLEAN)
ARCH_MD = "# Architecture Definition\n\n1. Context.\n\n## Assumptions\n\nNone.\n"
SPRINT_MD = """---

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
"""


class _FakeLLM:
    """Sequential scripted client with the counters the engine reads."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._i = 0
        self.budget_usd = 100.0
        self.tokens_used = 0
        self.cost_used = 0.0
        self.cache_creation_tokens_used = 0
        self.cache_read_tokens_used = 0

    def remaining(self) -> float:
        return self.budget_usd - self.cost_used

    def _next(self) -> SimpleNamespace:
        text = self._responses[self._i]
        self._i += 1
        return SimpleNamespace(text=text)

    def call(self, *_a, **_k) -> SimpleNamespace:
        return self._next()

    def call_messages(self, *_a, **_k) -> SimpleNamespace:
        return self._next()


def _declarative_loop() -> Loop:
    return Loop(
        stages=[
            Stage(persona=PMGenerator(), gate=CriticGate()),
            Stage(persona=ArchitectureGenerator(), gate=ArtifactGate("architecture_definition")),
            Stage(
                persona=SprintBreakdownGenerator(),
                gate=ArtifactGate("sprint_plans", parse_json="list", require_nonempty_parse=True),
            ),
        ],
        impact_reentry={"architecture": 1, "plan": 2},
    )


def _initial_state(run_id: str) -> State:
    return State(
        schema_version=2,
        run_id=run_id,
        stage_history=[],
        artifacts={"human_input": "We need password reset."},
    )


def _responses() -> list[str]:
    return [PM_JSON, ARCH_MD, SPRINT_MD]


def test_declarative_pipeline_completes_on_happy_path() -> None:
    final = run_loop(_declarative_loop(), _initial_state("run-classic"), _FakeLLM(_responses()))
    assert final.status is RunStatus.COMPLETED
    assert (
        json.loads(final.artifacts["project_spec"])["problem_statement"]
        == "value for problem_statement"
    )
    assert final.artifacts["architecture_definition"] == ARCH_MD
    assert len(json.loads(final.artifacts["sprint_plans"])) == 1
    assert len(json.loads(final.artifacts["task_manifest"])) == 1


def test_declarative_pipeline_identical_across_engines() -> None:
    classic = run_loop(_declarative_loop(), _initial_state("run-a"), _FakeLLM(_responses()))
    graph = run_graph_loop(_declarative_loop(), _initial_state("run-b"), _FakeLLM(_responses()))

    for key in ("project_spec", "architecture_definition", "sprint_plans", "task_manifest"):
        assert classic.artifacts[key] == graph.artifacts[key], key
    assert classic.status is graph.status is RunStatus.COMPLETED
