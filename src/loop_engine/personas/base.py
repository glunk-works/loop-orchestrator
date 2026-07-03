from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loop_engine.core.state import State

if TYPE_CHECKING:
    from loop_engine.tools.llm.client import LLMClient


class BasePersona(ABC):
    @abstractmethod
    def run(self, state: State, llm_client: LLMClient) -> State: ...
