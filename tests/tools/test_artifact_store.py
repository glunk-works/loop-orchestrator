import locale
import sys
from pathlib import Path

import pytest

from loop_engine.core.state import State, default_artifact_path
from loop_engine.tools import artifact_store
from loop_engine.tools.artifact_store import has_artifact, publish_artifacts


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(**artifacts: str) -> State:
    return State(schema_version=3, run_id="run-001", stage_history=[], artifacts=artifacts)


def test_publish_writes_bodies_to_disk() -> None:
    state = _state(project_spec='{"scope": "x"}')
    result = publish_artifacts(state)

    assert result is None
    path = Path(default_artifact_path("run-001", "project_spec"))
    assert path.read_text() == '{"scope": "x"}'


def test_publish_is_idempotent_for_unchanged_bodies(monkeypatch) -> None:
    state = _state(spec="body")
    publish_artifacts(state)

    calls = []
    monkeypatch.setattr(artifact_store, "write_artifact", lambda content, path: calls.append(path))
    publish_artifacts(state)
    assert calls == []


def test_publish_overwrites_on_body_change() -> None:
    state = _state(spec="v1")
    publish_artifacts(state)

    changed = state.model_copy(update={"artifacts": {"spec": "v2"}})
    publish_artifacts(changed)

    path = Path(default_artifact_path("run-001", "spec"))
    assert path.read_text() == "v2"


def test_publish_lands_bodies_under_docs_artifacts_run_id() -> None:
    # The property flows/maintenance depends on to ship design docs in the PR.
    state = _state(architecture="design doc body", sprint_plan="plan body")
    publish_artifacts(state)

    run_dir = Path("docs/artifacts/run-001")
    assert (run_dir / "architecture").read_text() == "design doc body"
    assert (run_dir / "sprint_plan").read_text() == "plan body"


@pytest.mark.parametrize(
    "ctype_locale",
    [
        None,
        pytest.param(
            "C",
            marks=pytest.mark.skipif(
                sys.flags.utf8_mode,
                reason="PEP 686 UTF-8 mode (default in 3.15) makes "
                "locale.setlocale(LC_CTYPE, 'C') not change the process's default text "
                "encoding, so this parametrization would silently stop exercising the "
                "non-UTF-8-locale path this test exists to cover. The None case has no "
                "such dependency and must keep running (F32).",
            ),
        ),
    ],
)
def test_publish_is_idempotent_for_unchanged_non_ascii_body(monkeypatch, ctype_locale) -> None:
    # The "C" case forces the process's *default* text encoding (what any
    # bare read_text()/write_text() falls back to) to ASCII. It reproduces
    # F1 on a host whose locale default isn't UTF-8: without an explicit
    # encoding="utf-8" pinned at the write side, this body fails to write
    # at all under that default, so this parametrization fails without the
    # fix instead of passing regardless (the tautology this replaces).
    previous_locale = locale.setlocale(locale.LC_CTYPE)
    if ctype_locale is not None:
        locale.setlocale(locale.LC_CTYPE, ctype_locale)
    try:
        body = "spec: café — 日本語 😀"
        state = _state(spec=body)
        publish_artifacts(state)

        path = Path(default_artifact_path("run-001", "spec"))
        assert path.read_bytes() == body.encode("utf-8")

        calls = []
        monkeypatch.setattr(
            artifact_store, "write_artifact", lambda content, path: calls.append(path)
        )
        publish_artifacts(state)
        assert calls == []
        assert path.read_bytes() == body.encode("utf-8")
    finally:
        locale.setlocale(locale.LC_CTYPE, previous_locale)


def test_publish_overwrites_a_corrupt_non_utf8_artifact_without_raising() -> None:
    # F13: the idempotence check used to be path.read_text(encoding="utf-8")
    # == body, which raises UnicodeDecodeError if the on-disk artifact isn't
    # valid UTF-8 -- crashing publish_artifacts on a file it was about to
    # overwrite anyway. Comparing bytes instead can never raise: invalid
    # bytes simply compare unequal to the encoded body and get overwritten.
    state = _state(spec="v2")
    path = Path(default_artifact_path("run-001", "spec"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe not valid utf-8")

    publish_artifacts(state)

    assert path.read_bytes() == b"v2"


def test_has_artifact_reflects_nonempty_body() -> None:
    assert has_artifact(_state(spec="x"), "spec") is True
    assert has_artifact(_state(spec="  "), "spec") is False
    assert has_artifact(_state(), "spec") is False
