import ast
import hashlib
import hmac
import json
from pathlib import Path

from fastapi.testclient import TestClient

from loop_engine.trigger.app import create_app
from loop_engine.trigger.parse import RunRequest

TRIGGER_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine" / "trigger"

_DISALLOWED_WRITE_CALLS = {"open", "write_text", "write_bytes"}
_DISALLOWED_SUBPROCESS_MODULES = {"subprocess"}
_DISALLOWED_OS_CALLS = {
    "system",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execv",
    "execve",
    "execvp",
    "execvpe",
}


def _imports_keyring(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "keyring" or alias.name.startswith("keyring.") for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "keyring" or node.module.startswith("keyring."):
                return True
    return False


def _direct_write_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in _DISALLOWED_WRITE_CALLS:
            found.append(func.id)
        elif isinstance(func, ast.Attribute) and func.attr in {"write_text", "write_bytes"}:
            found.append(func.attr)
    return found


def _subprocess_surfaces(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                alias.name for alias in node.names if alias.name in _DISALLOWED_SUBPROCESS_MODULES
            )
        elif isinstance(node, ast.ImportFrom) and node.module in _DISALLOWED_SUBPROCESS_MODULES:
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "Popen":
                found.append("Popen")
            elif isinstance(func, ast.Attribute) and func.attr in _DISALLOWED_OS_CALLS:
                found.append(f"os.{func.attr}")
            elif isinstance(func, ast.Name) and func.id == "Popen":
                found.append("Popen")
    return found


def _trigger_modules() -> list[Path]:
    return sorted(TRIGGER_DIR.rglob("*.py"))


def test_trigger_package_imports_no_keyring() -> None:
    for path in _trigger_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        assert not _imports_keyring(tree), f"{path} imports keyring"


def test_trigger_package_writes_no_files_directly() -> None:
    for path in _trigger_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_write_calls(tree)
        assert not calls, f"{path} calls disallowed file-write function(s): {calls}"


def test_trigger_package_adds_no_subprocess_surface() -> None:
    for path in _trigger_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        surfaces = _subprocess_surfaces(tree)
        assert not surfaces, f"{path} introduces a subprocess surface: {surfaces}"


_SECRET = "test-webhook-secret-not-a-real-credential"


class _FakeDispatcher:
    def __init__(self) -> None:
        self.received: list[RunRequest] = []

    async def dispatch(self, request: RunRequest) -> None:
        self.received.append(request)


def test_signed_webhook_reaches_dispatcher_without_a_real_loop(monkeypatch) -> None:
    monkeypatch.setenv("LOOP_ENGINE_WEBHOOK_SECRET", _SECRET)
    fake = _FakeDispatcher()
    client = TestClient(create_app(dispatcher=fake))

    payload = {
        "action": "labeled",
        "label": {"name": "agent-action"},
        "issue": {"number": 5, "title": "Ship it", "body": "Please ship it."},
        "repository": {"full_name": "acme/widgets"},
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(_SECRET.encode(), body, hashlib.sha256).hexdigest()

    resp = client.post(
        "/webhook",
        content=body,
        headers={"X-GitHub-Event": "issues", "X-Hub-Signature-256": signature},
    )

    assert resp.status_code == 202
    assert len(fake.received) == 1
    assert fake.received[0].human_input == "Ship it\n\nPlease ship it."
    assert fake.received[0].repo_full_name == "acme/widgets"
    assert fake.received[0].issue_number == 5
