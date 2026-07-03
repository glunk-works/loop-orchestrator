import ssl
from pathlib import Path

from loop_engine.tools.llm.client import LLMClient

CLIENT_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "loop_engine"
    / "tools"
    / "llm"
    / "client.py"
)


def test_client_source_never_disables_tls_verification() -> None:
    source = CLIENT_SOURCE_PATH.read_text()
    assert "verify=False" not in source
    assert "verify_ssl=False" not in source
    assert "CERT_NONE" not in source


def test_underlying_http_transport_has_certificate_verification_enabled(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_tokens=1000)

    ssl_context = client._anthropic._client._transport._pool._ssl_context
    assert ssl_context.verify_mode == ssl.CERT_REQUIRED
