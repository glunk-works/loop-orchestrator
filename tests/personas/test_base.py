import pytest

from loop_engine.personas.base import BasePersona


def test_subclass_without_run_cannot_be_instantiated() -> None:
    class IncompletePersona(BasePersona):
        pass

    with pytest.raises(TypeError):
        IncompletePersona()
