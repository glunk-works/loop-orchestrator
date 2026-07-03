import anthropic
import keyring
from pydantic import BaseModel

_KEYRING_SERVICE = "loop-engine"
_KEYRING_USERNAME = "anthropic_api_key"


class MissingCredentialError(Exception):
    pass


class BudgetExceededError(Exception):
    pass


class LLMResponse(BaseModel):
    text: str
    tokens_used: int


def _estimate_tokens(prompt: str) -> int:
    # Rough pre-flight heuristic (~4 chars/token). The authoritative count
    # used to update _tokens_used always comes from the API response itself.
    return max(1, len(prompt) // 4)


class LLMClient:
    def __init__(self, budget_tokens: int) -> None:
        api_key = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        if api_key is None:
            raise MissingCredentialError(
                f"No API key found in keyring for service={_KEYRING_SERVICE!r}, "
                f"username={_KEYRING_USERNAME!r}."
            )
        self._api_key = api_key
        self._anthropic = anthropic.Anthropic(api_key=api_key)
        self.budget_tokens = budget_tokens
        self._tokens_used = 0

    def call(self, prompt: str, *, model: str, max_tokens: int = 1024, **kwargs) -> LLMResponse:
        estimated_tokens = _estimate_tokens(prompt) + max_tokens
        if self._tokens_used + estimated_tokens > self.budget_tokens:
            remaining = self.budget_tokens - self._tokens_used
            raise BudgetExceededError(
                f"Estimated {estimated_tokens} tokens would exceed the "
                f"{remaining} tokens remaining in the run budget."
            )

        response = self._anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        actual_tokens = response.usage.input_tokens + response.usage.output_tokens
        self._tokens_used += actual_tokens
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return LLMResponse(text=text, tokens_used=actual_tokens)
