from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loop_engine.core.state import Question, State

if TYPE_CHECKING:
    from loop_engine.tools.llm.client import LLMClient


class BasePersona(ABC):
    # Artifact keys this persona reads / writes. The engine pre-checks
    # `consumes` before dispatch (a missing input fails the run explicitly
    # instead of surfacing as a KeyError deep inside a prompt build) and
    # treats `produces` as the minimum contract its gate can rely on.
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()

    @abstractmethod
    def run(self, state: State, llm_client: LLMClient, findings: list[str] | None = None) -> State:
        """Produce this persona's artifact(s).

        `findings` carries gate feedback or resolved-question answers on a
        revision pass; personas fold them into the prompt rather than
        restarting blind.
        """

    def resolve_questions(
        self, questions: list[Question], state: State, llm_client: LLMClient
    ) -> list[Question]:
        """Attempt to answer escalated questions from a lower stage using this
        persona's own artifact as context. Default: resolves nothing — the
        engine escalates the still-unresolved remainder up the chain."""
        return questions
