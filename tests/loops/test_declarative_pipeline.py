"""The declarative document personas drive a full PM → Architect → Sprint
Breakdown pipeline to the expected artifacts on the happy path."""

import json
from types import SimpleNamespace

import pytest

from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import ArtifactGate
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import IssueRef, RunStatus, State
from loop_engine.loops.default.loop import build_default_loop
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
    final = run_graph_loop(
        _declarative_loop(), _initial_state("run-classic"), _FakeLLM(_responses())
    )
    assert final.status is RunStatus.COMPLETED
    assert (
        json.loads(final.artifacts["project_spec"])["problem_statement"]
        == "value for problem_statement"
    )
    assert final.artifacts["architecture_definition"] == ARCH_MD
    assert len(json.loads(final.artifacts["sprint_plans"])) == 1
    assert len(json.loads(final.artifacts["task_manifest"])) == 1


def test_default_loop_pm_stage_escalates_after_exhausting_revisions(monkeypatch) -> None:
    # A non-converging PM (the critic keeps finding a shrinking-but-never-empty
    # set of blank fields) must exhaust its 4-revision budget and escalate to a
    # human issue (review finding #2/#3), not raise StageGateFailedError — PM's
    # only resolver is the human, so a hard fail there is a dead end.
    monkeypatch.setenv("LOOP_ENGINE_PERSONAS", "declarative")
    monkeypatch.delenv("LOOP_ENGINE_CODER", raising=False)
    loop = build_default_loop()
    pm_stage = loop.stages[0]
    assert pm_stage.max_revisions == 4
    assert pm_stage.escalate_on_exhaustion is True

    # Initial extraction: every field blank. Each of the 4 followup revisions
    # fills exactly one more field, so the critic's finding set keeps shrinking
    # (never repeats, never empties) all the way through the revision budget.
    responses = [
        json.dumps({}),
        json.dumps({"problem_statement": "value"}),
        json.dumps({"purpose_and_goals": "value"}),
        json.dumps({"target_users": "value"}),
        json.dumps({"in_scope": "value"}),
    ]
    single_stage_loop = Loop(stages=[pm_stage])

    final = run_graph_loop(single_stage_loop, _initial_state("run-pm-exhaust"), _FakeLLM(responses))

    assert final.status is RunStatus.AWAITING_ISSUE
    assert final.pending_issue is not None
