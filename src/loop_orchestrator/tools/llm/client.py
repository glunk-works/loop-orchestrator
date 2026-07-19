from collections.abc import Callable

import anthropic
import keyring
from pydantic import BaseModel

from loop_orchestrator.tools.env_compat import getenv_compat
from loop_orchestrator.tools.llm import pricing

_KEYRING_SERVICE = "loop-orchestrator"
# Back-compat: the keyring service was renamed loop-engine -> loop-orchestrator
# with the sprint-42 package rename. A key stored under the old service name
# (including in a persisted keyring_data.enc that survives container rebuilds)
# still resolves via this fallback, so the rename never strands an already-
# configured credential. Re-run keyring setup to migrate it to the new name.
_KEYRING_SERVICE_LEGACY = "loop-engine"
_KEYRING_USERNAME = "anthropic_api_key"

# Narrowly-scoped, double-gated escape hatch for CI/automation contexts where
# a container has no OS-native keyring backend and injecting a pre-encrypted
# keyring file is impractical. Both variables must be set together — a
# leftover LOOP_ORCHESTRATOR_CI_API_KEY in an interactive shell can't silently
# bypass keyring on its own. Everywhere else (interactive use, the prod
# container's primary path), the encrypted file-based keyring backend is
# used instead; this fallback changes nothing about that path.
_CI_OPT_IN_ENV_VAR = "LOOP_ORCHESTRATOR_ALLOW_ENV_CREDENTIAL"
_CI_OPT_IN_VALUE = "1"
_CI_API_KEY_ENV_VAR = "LOOP_ORCHESTRATOR_CI_API_KEY"


class MissingCredentialError(Exception):
    pass


class BudgetExceededError(Exception):
    pass


class TruncatedResponseError(Exception):
    """The model hit max_tokens: the response is silently incomplete and must
    not be treated as a finished artifact by any downstream stage."""


class InvalidMessageSequenceError(Exception):
    """A message list ended with a non-user turn: a trailing assistant
    message is a prefill, which the model rejects — caught client-side
    before any transport spend."""


class ToolLoopExceededError(Exception):
    """A tool loop hit its iteration cap without the model finishing the
    turn. Like truncation, this fails the stage honestly instead of letting
    a half-finished result propagate."""


# Finite backstop on tool-loop iterations. The *primary* bound is the USD
# budget: every iteration makes a metered API call and re-checks the ledger
# (see run_tool_loop), so BudgetExceededError already stops a runaway loop.
# This cap only guards the degenerate case of many near-zero-cost iterations;
# it is set generously so it never guillotines an increment that is genuinely
# making progress (read → edit → run_tests → fix cycles legitimately need more
# than a handful of turns) — that is a job for the budget, not this backstop.
DEFAULT_MAX_TOOL_ITERATIONS = 40


class LLMResponse(BaseModel):
    text: str
    tokens_used: int
    cost_usd: float = 0.0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


def _estimate_tokens(prompt: str) -> int:
    # Rough pre-flight heuristic (~4 chars/token). The authoritative count
    # used to update the cost/token counters always comes from the API
    # response itself.
    return max(1, len(prompt) // 4)


# When the heuristic pre-flight estimate reaches this share of the remaining
# budget, spend one (free) count_tokens round-trip for an exact input count
# before deciding to abort. Far from the cap, the heuristic alone is enough.
_COUNT_TOKENS_GUARD_BAND = 0.5


def _build_system_param(system_blocks: list[str]) -> list[dict]:
    """Render system blocks with a cache breakpoint on the last block.

    Prompt caching is a prefix match: callers must keep these blocks
    byte-identical across calls (state-derived content only — never
    timestamps, findings, or attempt counters).
    """
    blocks: list[dict] = [{"type": "text", "text": text} for text in system_blocks]
    blocks[-1]["cache_control"] = {"type": "ephemeral"}
    return blocks


def _resolve_api_key() -> str | None:
    if getenv_compat(_CI_OPT_IN_ENV_VAR) == _CI_OPT_IN_VALUE:
        env_api_key = getenv_compat(_CI_API_KEY_ENV_VAR)
        if env_api_key is not None:
            return env_api_key
    key = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    if key is None:
        key = keyring.get_password(_KEYRING_SERVICE_LEGACY, _KEYRING_USERNAME)
    return key


class LLMClient:
    def __init__(self, budget_usd: float) -> None:
        api_key = _resolve_api_key()
        if api_key is None:
            raise MissingCredentialError(
                f"No API key found in keyring for service={_KEYRING_SERVICE!r}, "
                f"username={_KEYRING_USERNAME!r}."
            )
        self._api_key = api_key
        # Document-emitting personas run non-streaming at max_tokens up to
        # 64000; the SDK's default 10-minute timeout estimates that as
        # potentially too slow for a non-streaming call and raises ValueError
        # before ever sending the request. Widen it instead of migrating
        # every call site to streaming.
        self._anthropic = anthropic.Anthropic(api_key=api_key, timeout=2400.0)
        self.budget_usd = budget_usd
        self._tokens_used = 0
        self._cost_used = 0.0
        self._cache_creation_tokens_used = 0
        self._cache_read_tokens_used = 0

    @property
    def tokens_used(self) -> int:
        """Total tokens processed across all classes (input, output, cache
        writes, cache reads) — visibility, not the budget unit."""
        return self._tokens_used

    @property
    def cost_used(self) -> float:
        return self._cost_used

    @property
    def cache_creation_tokens_used(self) -> int:
        return self._cache_creation_tokens_used

    @property
    def cache_read_tokens_used(self) -> int:
        return self._cache_read_tokens_used

    def remaining(self) -> float:
        """Dollars left in the run budget. The single budget API: the engine
        checks this rather than reaching into private counters, and this class
        is the only place a budget decision is made."""
        return self.budget_usd - self._cost_used

    def _preflight(
        self,
        *,
        model: str,
        max_tokens: int,
        messages: list[dict],
        system_param: list[dict] | None,
        estimated_input_tokens: int,
    ) -> None:
        estimated_cost = pricing.estimate_cost_usd(model, estimated_input_tokens, max_tokens)

        if estimated_cost >= _COUNT_TOKENS_GUARD_BAND * self.remaining():
            # Near the cap the heuristic is too blunt to abort on: refine with
            # the token-counting endpoint. Never a new hard-failure mode — on
            # any error the heuristic estimate stands and the call proceeds to
            # the normal budget decision below.
            count_kwargs: dict = {"model": model, "messages": messages}
            if system_param is not None:
                count_kwargs["system"] = system_param
            try:
                counted = self._anthropic.messages.count_tokens(**count_kwargs).input_tokens
            except Exception:  # noqa: BLE001 — pre-flight refinement is best-effort by design
                counted = None
            if counted is not None:
                estimated_cost = pricing.estimate_cost_usd(model, counted, max_tokens)

        if estimated_cost > self.remaining():
            raise BudgetExceededError(
                f"Estimated ${estimated_cost:.4f} would exceed the "
                f"${self.remaining():.4f} remaining in the run budget."
            )

    def call(
        self,
        prompt: str,
        *,
        model: str,
        max_tokens: int = 1024,
        system_blocks: list[str] | None = None,
        **kwargs,
    ) -> LLMResponse:
        return self.call_messages(
            [{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            system_blocks=system_blocks,
            **kwargs,
        )

    def call_messages(
        self,
        messages: list[dict],
        *,
        model: str,
        max_tokens: int = 1024,
        system_blocks: list[str] | None = None,
        **kwargs,
    ) -> LLMResponse:
        _, result = self._request(
            messages,
            model=model,
            max_tokens=max_tokens,
            system_blocks=system_blocks,
            **kwargs,
        )
        return result

    def run_tool_loop(
        self,
        messages: list[dict],
        *,
        model: str,
        tools: list[dict],
        execute: Callable[[str, dict], str],
        max_tokens: int = 1024,
        system_blocks: list[str] | None = None,
        max_iterations: int = DEFAULT_MAX_TOOL_ITERATIONS,
    ) -> LLMResponse:
        """Bounded agentic loop: execute tool calls until the model finishes.

        The client stays the sole budget owner — every iteration runs the
        same pre-flight and cost debit as a plain call, so a loop that grows
        too expensive raises BudgetExceededError mid-flight. Executor
        exceptions are surfaced to the model as is_error tool results, never
        crashes. Exceeding max_iterations fails honestly (like truncation)
        rather than silently returning a half-finished turn.
        """
        working = list(messages)
        for _ in range(max_iterations):
            # The per-call pre-flight estimates the NEXT call; it cannot see
            # that previous iterations already spent the run out. Check the
            # ledger directly, exactly like the engine does between stages.
            if self.remaining() <= 0:
                raise BudgetExceededError(
                    f"Run budget exhausted mid-tool-loop (${self.remaining():.4f} remaining)."
                )
            response, result = self._request(
                working,
                model=model,
                max_tokens=max_tokens,
                system_blocks=system_blocks,
                tools=tools,
            )
            if getattr(response, "stop_reason", None) != "tool_use":
                return result

            tool_results: list[dict] = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                try:
                    output = execute(block.name, block.input)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": output}
                    )
                except Exception as exc:  # noqa: BLE001 — executor failures feed back to the model
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"{type(exc).__name__}: {exc}",
                            "is_error": True,
                        }
                    )

            # The assistant turn (with its tool_use blocks) and ALL tool
            # results in a single user message, per the tool-use contract.
            working = [
                *working,
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results},
            ]

        raise ToolLoopExceededError(
            f"Tool loop did not converge within {max_iterations} iterations; "
            "failing the stage instead of returning a half-finished turn."
        )

    def _request(
        self,
        messages: list[dict],
        *,
        model: str,
        max_tokens: int = 1024,
        system_blocks: list[str] | None = None,
        **kwargs,
    ) -> tuple[object, LLMResponse]:
        if not messages or messages[-1].get("role") != "user":
            raise InvalidMessageSequenceError(
                "messages must end with a user turn — a trailing assistant "
                "message is a prefill, which the model rejects with a 400."
            )

        system_param = _build_system_param(system_blocks) if system_blocks else None

        estimated_input = sum(
            _estimate_tokens(message["content"])
            for message in messages
            if isinstance(message.get("content"), str)
        ) + sum(_estimate_tokens(block) for block in system_blocks or [])
        self._preflight(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system_param=system_param,
            estimated_input_tokens=estimated_input,
        )

        request_kwargs = dict(kwargs)
        if system_param is not None:
            request_kwargs["system"] = system_param

        response = self._anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            **request_kwargs,
        )

        # Cache fields are absent on responses (and test doubles) that predate
        # caching; getattr-with-default keeps them equivalent to zero.
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cache_creation = getattr(response.usage, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(response.usage, "cache_read_input_tokens", 0) or 0

        turn_cost = pricing.cost_usd(model, input_tokens, output_tokens, cache_creation, cache_read)
        actual_tokens = input_tokens + output_tokens + cache_creation + cache_read
        self._tokens_used += actual_tokens
        self._cost_used += turn_cost
        self._cache_creation_tokens_used += cache_creation
        self._cache_read_tokens_used += cache_read

        if getattr(response, "stop_reason", None) == "max_tokens":
            raise TruncatedResponseError(
                f"Response hit the max_tokens={max_tokens} ceiling; the output is "
                "incomplete and would corrupt downstream stages if used."
            )

        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return response, LLMResponse(
            text=text,
            tokens_used=actual_tokens,
            cost_usd=turn_cost,
            cache_creation_input_tokens=cache_creation,
            cache_read_input_tokens=cache_read,
        )
