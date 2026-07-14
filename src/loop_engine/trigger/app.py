"""The webhook ASGI app: HMAC-verify -> parse -> dispatch.

The webhook is a run-trigger — a valid request causes the engine to execute
model-driven code — so signature verification is the trust boundary and must
be airtight: the raw body is read and HMAC-verified *before* any JSON
parsing. No secret is ever logged. `create_app` reads
`LOOP_ENGINE_WEBHOOK_SECRET` at construction and fails closed (raises) if it
is unset — the app must never fall open to unsigned requests. An
authenticated request whose body is not valid JSON returns `400` — it is
never allowed to 500.
"""

import hashlib
import hmac
import json
import os

from fastapi import FastAPI, Request
from fastapi.responses import Response

from loop_engine.trigger.dispatch import InProcessDispatcher, RunDispatcher
from loop_engine.trigger.parse import parse_event

_SIGNATURE_HEADER = "X-Hub-Signature-256"
_EVENT_HEADER = "X-GitHub-Event"


def _expected_signature(secret: str, raw_body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()


def _signature_is_valid(secret: str, raw_body: bytes, header_value: str | None) -> bool:
    if not header_value:
        return False
    return hmac.compare_digest(_expected_signature(secret, raw_body), header_value)


def create_app(dispatcher: RunDispatcher | None = None) -> FastAPI:
    """Build the webhook app. Fails closed: raises if
    `LOOP_ENGINE_WEBHOOK_SECRET` is unset, so the app never starts unsigned."""
    secret = os.environ.get("LOOP_ENGINE_WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError(
            "LOOP_ENGINE_WEBHOOK_SECRET is not set; refusing to start the "
            "webhook app unsigned (fail-closed)."
        )
    active_dispatcher = dispatcher if dispatcher is not None else InProcessDispatcher()

    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/webhook")
    async def webhook(request: Request) -> Response:
        raw_body = await request.body()
        if not _signature_is_valid(secret, raw_body, request.headers.get(_SIGNATURE_HEADER)):
            return Response(status_code=401)

        try:
            payload = json.loads(raw_body)
        except ValueError:
            return Response(status_code=400)
        event_name = request.headers.get(_EVENT_HEADER, "")
        run_request = parse_event(event_name, payload)
        if run_request is None:
            return Response(status_code=204)

        await active_dispatcher.dispatch(run_request)
        return Response(status_code=202)

    return app


app = create_app() if os.environ.get("LOOP_ENGINE_WEBHOOK_SECRET") else None
