"""The bounty loop skeleton (S46, P1-D3): structure, blast-radius re-entry,
an engine-driven green end-to-end run over the stub personas, and the two
new-package module-boundary asserts (mirroring `tests/trigger/test_boundaries.py`).
"""

import ast
import json
from pathlib import Path

import pytest

from loop_orchestrator.core.engine import Loop
from loop_orchestrator.core.gates import ArtifactGate
from loop_orchestrator.core.graph_engine import run_graph_loop
from loop_orchestrator.core.state import BountyRunState, RunStatus
from loop_orchestrator.loops.bounty.loop import BOUNTY_LOOP, build_bounty_loop
from loop_orchestrator.personas.bounty.recon import ReconPersona
from loop_orchestrator.personas.bounty.surface_map import SurfaceMapPersona
from tests.core.test_engine import _initial_state, _stub_llm_client

_SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "loop_orchestrator"
_LOOPS_BOUNTY_DIR = _SRC_ROOT / "loops" / "bounty"
_PERSONAS_BOUNTY_DIR = _SRC_ROOT / "personas" / "bounty"

_DISALLOWED_IMPORT_MODULES = {"keyring", "psycopg", "subprocess"}
_DISALLOWED_WRITE_CALLS = {"open", "write_text", "write_bytes"}


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_build_bounty_loop_is_two_stages_recon_then_surface_map() -> None:
    assert isinstance(BOUNTY_LOOP, Loop)
    assert [type(stage.persona) for stage in BOUNTY_LOOP.stages] == [
        ReconPersona,
        SurfaceMapPersona,
    ]


def test_bounty_loop_gates_are_json_typed_per_stage() -> None:
    recon_gate = BOUNTY_LOOP.stages[0].gate
    mapping_gate = BOUNTY_LOOP.stages[1].gate
    assert isinstance(recon_gate, ArtifactGate)
    assert recon_gate.artifact_key == "asset_inventory"
    assert recon_gate.parse_json == "list"
    assert isinstance(mapping_gate, ArtifactGate)
    assert mapping_gate.artifact_key == "surface_map"
    assert mapping_gate.parse_json == "object"


def test_bounty_loop_mapping_resolves_up_to_recon() -> None:
    loop = build_bounty_loop()
    recon_persona = loop.stages[0].persona
    assert [type(r) for r in loop.stages[1].resolvers] == [ReconPersona]
    # The re-entry Recon is the SAME instance the Recon stage runs, not a
    # second, disconnected ReconPersona.
    assert loop.stages[1].resolvers[0] is recon_persona
    assert loop.stages[0].resolvers == []


def test_bounty_loop_blast_radius_reentry_targets() -> None:
    assert BOUNTY_LOOP.impact_reentry == {"scope": 0, "surface": 1}


def test_bounty_loop_runs_green_end_to_end_with_stub_personas() -> None:
    initial_state = _initial_state("bounty-1").model_copy(
        update={"bounty": BountyRunState(target_id="target-001")}
    )

    final = run_graph_loop(build_bounty_loop(), initial_state, _stub_llm_client())

    assert final.status is RunStatus.COMPLETED
    assert json.loads(final.artifacts["asset_inventory"]) == []
    assert json.loads(final.artifacts["surface_map"]) == {}
    assert final.questions == []


def _bounty_package_modules() -> list[Path]:
    return sorted(_LOOPS_BOUNTY_DIR.rglob("*.py")) + sorted(_PERSONAS_BOUNTY_DIR.rglob("*.py"))


def _imports_disallowed_module(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                alias.name
                for alias in node.names
                if alias.name.split(".")[0] in _DISALLOWED_IMPORT_MODULES
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in _DISALLOWED_IMPORT_MODULES:
                found.append(node.module)
    return found


def _direct_write_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in _DISALLOWED_WRITE_CALLS:
            found.append(func.id)
        elif isinstance(func, ast.Attribute) and func.attr in {"write_text", "write_bytes"}:
            found.append(func.attr)
    return found


def _imports_tools_package(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                alias.name
                for alias in node.names
                if alias.name == "loop_orchestrator.tools"
                or alias.name.startswith("loop_orchestrator.tools.")
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "loop_orchestrator.tools" or node.module.startswith(
                "loop_orchestrator.tools."
            ):
                found.append(node.module)
    return found


def test_bounty_packages_import_no_keyring_psycopg_or_subprocess() -> None:
    for path in _bounty_package_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        found = _imports_disallowed_module(tree)
        assert not found, f"{path} imports disallowed module(s): {found}"


def test_bounty_packages_write_no_files_directly() -> None:
    for path in _bounty_package_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_write_calls(tree)
        assert not calls, f"{path} calls disallowed file-write function(s): {calls}"


def test_bounty_personas_import_nothing_from_tools() -> None:
    for path in sorted(_PERSONAS_BOUNTY_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        found = _imports_tools_package(tree)
        assert not found, f"{path} imports from tools/*: {found}"
