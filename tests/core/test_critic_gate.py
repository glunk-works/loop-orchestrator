"""CriticGate: the PM critic *checks* re-expressed as a structural stage gate."""

import ast
import json
from pathlib import Path

from loop_engine.core.gates import GateDecision
from loop_engine.core.state import State
from loop_engine.personas.pm.critic_gate import CriticGate
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS

_CLEAN = {field: f"value for {field}" for field in CHECKLIST_FIELDS}
_CLEAN["in_scope"] = "reset flow"
_CLEAN["out_of_scope"] = "sso"
_CLEAN["acceptance_criteria"] = "A user resets their password end to end within five minutes."


def _state(spec: dict) -> State:
    return State(
        schema_version=2,
        run_id="r",
        stage_history=[],
        artifacts={"project_spec": json.dumps({**spec, "revision_history": []})},
    )


def test_clean_spec_accepts() -> None:
    result = CriticGate()(_state(_CLEAN), "PMGenerator")
    assert result.decision is GateDecision.ACCEPT


def test_blank_field_revises_naming_that_field() -> None:
    spec = {**_CLEAN}
    spec["target_users"] = ""
    result = CriticGate()(_state(spec), "PMGenerator")
    assert result.decision is GateDecision.REVISE
    assert any(f.startswith("target_users:") for f in result.findings)


def test_missing_project_spec_revises() -> None:
    empty = State(schema_version=2, run_id="r", stage_history=[], artifacts={})
    result = CriticGate()(empty, "PMGenerator")
    assert result.decision is GateDecision.REVISE


def test_findings_are_deterministic_for_no_progress_guard() -> None:
    spec = {**_CLEAN}
    spec["security_and_risk_considerations"] = ""
    a = CriticGate()(_state(spec), "PMGenerator")
    b = CriticGate()(_state(spec), "PMGenerator")
    # Identical findings across calls: this equality is exactly what
    # execute_stage's no-progress→escalate guard relies on.
    assert a.findings == b.findings


def test_critic_gate_imports_no_pmpersona_class() -> None:
    src = Path(__file__).resolve().parents[2] / "src/loop_engine/personas/pm/critic_gate.py"
    tree = ast.parse(src.read_text())
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
    # The gate reuses the pure critic checks, never the PMPersona class module.
    assert "loop_engine.personas.pm.persona" not in imported
