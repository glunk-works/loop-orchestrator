"""The Ralph iteration cap — all that remains of the Coder mode module.

Phase 6 deleted `LOOP_ENGINE_CODER` (and with it `coder_mode`/`use_ralph_coder`):
Ralph is the only Coder. `LOOP_ENGINE_RALPH_MAX_ITERS` survives because it is
genuine runtime config, not migration scaffolding.
"""

import pytest

from loop_engine.personas.coder_iac.mode import (
    RALPH_MAX_ITERS_ENV_VAR,
    ralph_max_iterations,
)


def test_ralph_max_iterations_default(monkeypatch) -> None:
    monkeypatch.delenv(RALPH_MAX_ITERS_ENV_VAR, raising=False)
    assert ralph_max_iterations() == 30


def test_ralph_max_iterations_override(monkeypatch) -> None:
    monkeypatch.setenv(RALPH_MAX_ITERS_ENV_VAR, "7")
    assert ralph_max_iterations() == 7


@pytest.mark.parametrize("bad", ["0", "-3", "notanint"])
def test_ralph_max_iterations_rejects_bad_values(monkeypatch, bad) -> None:
    monkeypatch.setenv(RALPH_MAX_ITERS_ENV_VAR, bad)
    with pytest.raises(ValueError):
        ralph_max_iterations()
