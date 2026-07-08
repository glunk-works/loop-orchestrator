"""Persona execution-mode flag — the single reader of `LOOP_ENGINE_PERSONAS`.

Mirrors `coder_iac/mode.py` / `graph_engine.use_langgraph_engine()`: a
lightweight, stdlib-only selector so `loops/default/loop.py` can pick the
declarative wiring without an import cycle. Default (`classic`) keeps the three
document personas byte-identical; `declarative` selects the `GeneratorNode`
ports + the PM `CriticGate`.
"""

import os
from typing import Literal

PERSONAS_ENV_VAR = "LOOP_ENGINE_PERSONAS"

_CLASSIC = "classic"
_DECLARATIVE = "declarative"
_ALLOWED = (_CLASSIC, _DECLARATIVE)


def persona_mode() -> Literal["classic", "declarative"]:
    """The selected persona mode; unset/empty ⇒ `classic`. Unknown ⇒ ValueError."""
    raw = os.environ.get(PERSONAS_ENV_VAR, "").strip().lower()
    if not raw:
        return _CLASSIC
    if raw not in _ALLOWED:
        raise ValueError(
            f"{PERSONAS_ENV_VAR}={raw!r} is not a valid persona mode; expected one of {_ALLOWED}"
        )
    return raw  # type: ignore[return-value]


def use_declarative_personas() -> bool:
    """Whether the declarative `GeneratorNode` personas are selected."""
    return persona_mode() == _DECLARATIVE
