import sys
import types

from loop_engine.tools.slack_io import send_ephemeral_reply

_FAKE_TOKEN = "xoxb-fake-not-a-real-token"  # noqa: S105 -- fixture literal, not a real credential


def _install_fake_slack_sdk(monkeypatch, client_cls) -> None:
    fake_module = types.ModuleType("slack_sdk")
    fake_module.WebClient = client_cls
    monkeypatch.setitem(sys.modules, "slack_sdk", fake_module)


def test_send_ephemeral_reply_posts_to_the_configured_channel_and_user(monkeypatch) -> None:
    calls: list[tuple] = []

    class _Client:
        def __init__(self, token: str, timeout: int) -> None:
            calls.append(("init", token, timeout))

        def chat_postEphemeral(self, **kwargs) -> None:
            calls.append(("post", kwargs))

    _install_fake_slack_sdk(monkeypatch, _Client)

    send_ephemeral_reply(
        bot_token=_FAKE_TOKEN, channel_id="C123", user_id="U456", text="Run accepted."
    )

    assert calls[0] == ("init", _FAKE_TOKEN, 5)
    kind, kwargs = calls[1]
    assert kind == "post"
    assert kwargs == {"channel": "C123", "user": "U456", "text": "Run accepted."}


def test_send_ephemeral_reply_swallows_a_raising_client(monkeypatch, caplog) -> None:
    class _RaisingClient:
        def __init__(self, token: str, timeout: int) -> None:
            pass

        def chat_postEphemeral(self, **kwargs) -> None:
            raise RuntimeError("simulated Slack outage")

    _install_fake_slack_sdk(monkeypatch, _RaisingClient)

    with caplog.at_level("WARNING"):
        send_ephemeral_reply(
            bot_token=_FAKE_TOKEN, channel_id="C123", user_id="U456", text="Run accepted."
        )

    assert _FAKE_TOKEN not in caplog.text
