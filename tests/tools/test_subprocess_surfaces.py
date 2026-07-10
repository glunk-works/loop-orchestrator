"""Repo-wide static assertion (Phase 5 sprint 24): subprocess/Popen/os.exec*
usage is confined to exactly the sanctioned surfaces named in `CLAUDE.md`'s
enforced-module-boundaries section. This moved from three surfaces to four
in sprint 24 with the addition of `tools/git_io`'s local `git` — nothing
else in `src/loop_engine` may shell out."""

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"

# path -> the sanctioned surface it belongs to. issue_io and repo_io are two
# consumers of the *same* `gh` surface (repo_io adds no fifth); each other
# module is its own distinct surface. Four distinct surface names total.
_SANCTIONED_SUBPROCESS_MODULES: dict[Path, str] = {
    SRC_ROOT / "tools" / "coder_tools" / "run_tests.py": "pytest",
    SRC_ROOT / "tools" / "issue_io" / "github.py": "gh",
    SRC_ROOT / "tools" / "repo_io" / "github.py": "gh",
    SRC_ROOT / "tools" / "worktree" / "manager.py": "git worktree",
    SRC_ROOT / "tools" / "git_io" / "local.py": "git",
}

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


def _shells_out(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "subprocess" for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            return True
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "Popen":
                return True
            if isinstance(func, ast.Name) and func.id == "Popen":
                return True
            if isinstance(func, ast.Attribute) and func.attr in _DISALLOWED_OS_CALLS:
                return True
    return False


def _all_source_modules() -> list[Path]:
    return sorted(SRC_ROOT.rglob("*.py"))


def test_subprocess_surfaces_are_confined_to_the_sanctioned_modules() -> None:
    shelling_modules = {
        path
        for path in _all_source_modules()
        if _shells_out(ast.parse(path.read_text(), filename=str(path)))
    }
    assert shelling_modules == set(_SANCTIONED_SUBPROCESS_MODULES)


def test_exactly_four_sanctioned_subprocess_surfaces() -> None:
    assert len(set(_SANCTIONED_SUBPROCESS_MODULES.values())) == 4
    assert SRC_ROOT / "tools" / "git_io" / "local.py" in _SANCTIONED_SUBPROCESS_MODULES
    assert _SANCTIONED_SUBPROCESS_MODULES[SRC_ROOT / "tools" / "git_io" / "local.py"] == "git"


def test_scaffold_is_a_file_write_surface_not_a_fifth_subprocess_surface() -> None:
    # Sprint 25 added `tools/scaffold` as the SECOND file-write surface (see
    # `tests/tools/test_state_io_boundary.py`) -- it must not also become a
    # fifth subprocess surface. It's deliberately absent from the sanctioned
    # dict, and `test_subprocess_surfaces_are_confined_to_the_sanctioned_modules`
    # would fail if `writer.py` ever imported `subprocess`.
    scaffold_writer = SRC_ROOT / "tools" / "scaffold" / "writer.py"
    assert scaffold_writer not in _SANCTIONED_SUBPROCESS_MODULES
    assert not _shells_out(ast.parse(scaffold_writer.read_text(), filename=str(scaffold_writer)))
