import json
import logging
from types import SimpleNamespace

from loop_engine.core.engine import run_loop
from loop_engine.core.state import State
from loop_engine.personas.base import BasePersona


class StubPersona(BasePersona):
    def run(self, state: State, llm_client) -> State:
        llm_client._tokens_used += 10
        return state


def _initial_state() -> State:
    return State(schema_version=1, run_id="run-1", stage_history=[], artifacts={})


def test_run_loop_emits_json_log_line_per_stage(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    llm_client = SimpleNamespace(_tokens_used=0, budget_tokens=1000)
    personas = [StubPersona(), StubPersona(), StubPersona()]

    with caplog.at_level(logging.INFO, logger="loop_engine.cost"):
        run_loop(personas, _initial_state(), llm_client)

    records = [r for r in caplog.records if r.name == "loop_engine.cost"]
    assert len(records) == 3

    for record in records:
        payload = json.loads(record.message)
        assert set(payload) == {"stage_name", "tokens_used", "cost_usd"}
        assert payload["tokens_used"] == 10
