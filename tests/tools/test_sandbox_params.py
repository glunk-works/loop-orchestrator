"""Phase 3b inert seam: the sandboxed coder-tools launch params.

These are deterministic argv-shape tests — no container or MCP server is
spawned (there is no runtime in this environment, and `unshare -Ur` is denied).
They assert the launch parameters and the never-degrade-to-in-process guards.
"""

import shutil

import pytest

from loop_engine.tools.isolation import IsolationUnavailableError
from loop_engine.tools.mcp import (
    build_coder_tool_provider,
    container_server_params,
    sandbox_server_params,
)
from loop_engine.tools.mcp import provider as provider_module

_MODULE = provider_module._CODER_TOOLS_SERVER_MODULE


def _fake_which(present: set[str]):
    return lambda cmd: f"/usr/bin/{cmd}" if cmd in present else None


@pytest.fixture
def _docker_available(monkeypatch):
    monkeypatch.setattr(shutil, "which", _fake_which({"docker"}))
    monkeypatch.delenv("LOOP_ENGINE_CONTAINER_RUNTIME", raising=False)
    monkeypatch.setenv("LOOP_ENGINE_DEV_IMAGE", "loop-engine-dev:latest")
    monkeypatch.setenv("LOOP_ENGINE_SANDBOX_UID", "1000:1000")


def test_container_params_exact_argv(_docker_available) -> None:
    params = container_server_params("/wt/run-1")
    wt = "/wt/run-1"
    assert params.command == "docker"
    assert params.args == [
        "run",
        "--rm",
        "-i",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp",  # noqa: S108 — asserting the container tmpfs mount target, not a host temp path
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        "1000:1000",
        "-v",
        f"{wt}:{wt}:rw",
        "-w",
        wt,
        "loop-engine-dev:latest",
        "python",
        "-m",
        _MODULE,
    ]
    assert params.cwd is None


def test_container_mounts_only_the_worktree(_docker_available) -> None:
    """The single bind mount is the security contract: only the worktree, and
    nothing else (no repo root, no state/, no host paths)."""
    args = container_server_params("/wt/run-1").args
    bind_indices = [i for i, a in enumerate(args) if a == "-v"]
    assert len(bind_indices) == 1
    assert args[bind_indices[0] + 1] == "/wt/run-1:/wt/run-1:rw"
    assert "--network" in args and args[args.index("--network") + 1] == "none"
    assert "--cap-drop" in args and args[args.index("--cap-drop") + 1] == "ALL"
    assert "--read-only" in args


def test_container_uses_podman_when_only_podman_present(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which({"podman"}))
    monkeypatch.delenv("LOOP_ENGINE_CONTAINER_RUNTIME", raising=False)
    monkeypatch.setenv("LOOP_ENGINE_DEV_IMAGE", "img:1")
    assert container_server_params("/wt").command == "podman"


def test_container_runtime_override_must_be_supported(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which({"docker"}))
    monkeypatch.setenv("LOOP_ENGINE_CONTAINER_RUNTIME", "lxc")
    monkeypatch.setenv("LOOP_ENGINE_DEV_IMAGE", "img:1")
    with pytest.raises(IsolationUnavailableError):
        container_server_params("/wt")


def test_container_params_requires_runtime(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which(set()))
    monkeypatch.delenv("LOOP_ENGINE_CONTAINER_RUNTIME", raising=False)
    monkeypatch.setenv("LOOP_ENGINE_DEV_IMAGE", "img:1")
    with pytest.raises(IsolationUnavailableError, match="no container runtime"):
        container_server_params("/wt")


def test_container_params_requires_dev_image(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which({"docker"}))
    monkeypatch.delenv("LOOP_ENGINE_CONTAINER_RUNTIME", raising=False)
    monkeypatch.delenv("LOOP_ENGINE_DEV_IMAGE", raising=False)
    with pytest.raises(IsolationUnavailableError, match="LOOP_ENGINE_DEV_IMAGE"):
        container_server_params("/wt")


def test_sandbox_params_exact_argv(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which({"bwrap"}))
    params = sandbox_server_params("/wt/run-1")
    wt = "/wt/run-1"
    assert params.command == "bwrap"
    assert params.args == [
        "--unshare-all",
        "--die-with-parent",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--ro-bind",
        "/bin",
        "/bin",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",  # noqa: S108 — asserting the bwrap tmpfs mount target, not a host temp path
        "--bind",
        wt,
        wt,
        "--chdir",
        wt,
        "python",
        "-m",
        _MODULE,
    ]


def test_sandbox_only_writable_bind_is_worktree(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which({"bwrap"}))
    args = sandbox_server_params("/wt/run-1").args
    bind_indices = [i for i, a in enumerate(args) if a == "--bind"]
    assert len(bind_indices) == 1
    assert args[bind_indices[0] + 1 : bind_indices[0] + 3] == ["/wt/run-1", "/wt/run-1"]
    assert "--unshare-all" in args  # includes the net namespace → no network


def test_sandbox_params_requires_bwrap(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which(set()))
    with pytest.raises(IsolationUnavailableError, match="bwrap"):
        sandbox_server_params("/wt")


def test_provider_selects_container_under_container_mode(monkeypatch, _docker_available) -> None:
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")
    provider = build_coder_tool_provider(cwd="/wt/run-1")
    assert provider._servers[0].command == "docker"


def test_provider_selects_bwrap_under_sandbox_mode(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", _fake_which({"bwrap"}))
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "sandbox")
    provider = build_coder_tool_provider(cwd="/wt/run-1")
    assert provider._servers[0].command == "bwrap"


def test_provider_defaults_to_local_subprocess(monkeypatch) -> None:
    import sys

    monkeypatch.delenv("LOOP_ENGINE_ISOLATION", raising=False)
    provider = build_coder_tool_provider(cwd="/wt/run-1")
    assert provider._servers[0].command == sys.executable


def test_container_mode_never_falls_back_to_in_process(monkeypatch) -> None:
    """A missing runtime under container mode raises — it must never silently
    build a provider that would run untrusted code in-process."""
    monkeypatch.setattr(shutil, "which", _fake_which(set()))
    monkeypatch.delenv("LOOP_ENGINE_CONTAINER_RUNTIME", raising=False)
    monkeypatch.setenv("LOOP_ENGINE_DEV_IMAGE", "img:1")
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")
    with pytest.raises(IsolationUnavailableError):
        build_coder_tool_provider(cwd="/wt/run-1")
