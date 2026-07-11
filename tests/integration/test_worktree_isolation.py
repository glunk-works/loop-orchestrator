"""Phase 3a: the engine runs identically with worktree isolation on, and places
artifacts vs. snapshots on the two sides of the worktree boundary (D2)."""

import subprocess
from types import SimpleNamespace

import pytest

from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import ArtifactGate
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import RunStatus, State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.worktree import worktree_run


class AppendArtifactPersona(BasePersona):
    def __init__(self, key: str) -> None:
        self._key = key

    def run(self, state: State, llm_client, findings=None) -> State:
        return state.model_copy(update={"artifacts": {**state.artifacts, self._key: "done"}})


def _loop(keys: list[str]) -> Loop:
    return Loop(
        stages=[Stage(persona=AppendArtifactPersona(k), gate=ArtifactGate(k)) for k in keys]
    )


def _client() -> SimpleNamespace:
    c = SimpleNamespace(
        budget_usd=10.0,
        tokens_used=0,
        cost_used=0.0,
        cache_creation_tokens_used=0,
        cache_read_tokens_used=0,
    )
    c.remaining = lambda: c.budget_usd - c.cost_used
    return c


def _state(run_id: str) -> State:
    return State(schema_version=2, run_id=run_id, stage_history=[], artifacts={})


@pytest.fixture
def repo(tmp_path, monkeypatch):
    init_cmds = (
        ["init", "-b", "main"],
        ["config", "user.email", "t@t"],
        ["config", "user.name", "t"],
    )
    for args in init_cmds:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "seed.txt"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=tmp_path, check=True, capture_output=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


ENGINES = [run_graph_loop]


@pytest.mark.parametrize("engine", ENGINES)
def test_isolation_on_matches_isolation_off(engine, repo, monkeypatch):
    monkeypatch.delenv("LOOP_ENGINE_ISOLATION", raising=False)
    off = engine(_loop(["a", "b"]), _state("off"), _client())

    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "worktree")
    with worktree_run("onrun"):
        on = engine(_loop(["a", "b"]), _state("onrun"), _client())

    assert on.status is off.status is RunStatus.COMPLETED
    assert on.artifacts == off.artifacts == {"a": "done", "b": "done"}


@pytest.mark.parametrize("engine", ENGINES)
def test_snapshots_in_main_checkout_artifacts_in_worktree(engine, repo, monkeypatch):
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "worktree")
    run_id = "splitrun"
    with worktree_run(run_id) as wt:
        engine(_loop(["a"]), _state(run_id), _client())

    # Snapshots stay in the orchestrator's main checkout.
    snapshots = sorted((repo / "state" / run_id).glob("*.json"))
    assert snapshots, "expected snapshots under the main checkout's state/"
    assert not (wt / "state").exists(), "snapshots must not leak into the worktree"

    # Mirrored artifact bodies live in the worktree.
    assert (wt / "docs" / "artifacts" / run_id / "a").is_file()
    assert not (repo / "docs" / "artifacts" / run_id / "a").exists()
