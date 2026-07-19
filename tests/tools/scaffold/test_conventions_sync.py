"""Sync-guard: the bundled `tools/scaffold` conventions template must stay
byte-identical to the dev-facing `.ai/context/conventions.md` so the
managed-repo copy and the source doc never silently drift."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_bundled_claude_md_is_byte_identical_to_ai_context_conventions() -> None:
    bundled = _REPO_ROOT / "src/loop_orchestrator/tools/scaffold/templates/CLAUDE.md"
    source = _REPO_ROOT / ".ai/context/conventions.md"
    assert bundled.read_bytes() == source.read_bytes()
