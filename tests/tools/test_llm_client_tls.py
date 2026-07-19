import ssl
from pathlib import Path

from loop_orchestrator.tools.llm.client import LLMClient

CLIENT_SOURCE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "loop_orchestrator"
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

    client = LLMClient(budget_usd=1.0)

    ssl_context = client._anthropic._client._transport._pool._ssl_context
    assert ssl_context.verify_mode == ssl.CERT_REQUIRED
