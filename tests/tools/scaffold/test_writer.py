"""Hermetic coverage for `tools/scaffold.write_skeleton` against a
`tmp_path` tree — no real clone, no network. See
`test_conventions_sync.py` for the bundled/`.ai` `CLAUDE.md` parity guard."""

from pathlib import Path

import pytest

from loop_engine.tools.scaffold import write_skeleton


@pytest.fixture
def tree(tmp_path, monkeypatch):
    dest = tmp_path / "demo"
    dest.mkdir()
    monkeypatch.chdir(tmp_path)
    return dest


def test_write_skeleton_writes_the_full_python_file_set(tree):
    written = write_skeleton("demo", kind="python", pkg_name="demo", repo_name="demo")

    assert set(written) == {
        "pyproject.toml",
        "src/demo/__init__.py",
        "tests/test_smoke.py",
        "README.md",
        ".gitignore",
        "CLAUDE.md",
    }
    for rel in written:
        assert (tree / rel).is_file()


def test_write_skeleton_substitutes_pkg_name_and_repo_name(tree):
    write_skeleton("demo", kind="python", pkg_name="demo", repo_name="demo-widgets")

    pyproject = (tree / "pyproject.toml").read_text()
    assert 'name = "demo-widgets"' in pyproject
    assert "__REPO_NAME__" not in pyproject
    assert "__PKG_NAME__" not in pyproject

    init_py = (tree / "src" / "demo" / "__init__.py").read_text()
    assert "demo-widgets" in init_py

    readme = (tree / "README.md").read_text()
    assert "demo-widgets" in readme


def test_write_skeleton_claude_md_is_byte_identical_to_bundled_template(tree):
    write_skeleton("demo", kind="python", pkg_name="demo", repo_name="demo")

    from importlib import resources

    bundled = (
        resources.files("loop_engine.tools.scaffold") / "templates" / "CLAUDE.md"
    ).read_text()
    assert (tree / "CLAUDE.md").read_text() == bundled


@pytest.mark.parametrize(
    "bad_tree",
    ["/abs/path", "demo/../escape", "../outside"],
)
def test_invalid_tree_argument_raises_value_error(tree, bad_tree):
    with pytest.raises(ValueError):
        write_skeleton(bad_tree, kind="python", pkg_name="demo", repo_name="demo")


@pytest.mark.parametrize(
    "bad_pkg_name,expected_dir",
    [
        ("de-mo", "src/de_mo/__init__.py"),
        ("2demo", "src/_2demo/__init__.py"),
        ("../../etc", "src/______etc/__init__.py"),
    ],
)
def test_pkg_name_is_sanitized_to_a_safe_identifier_no_escape(tree, bad_pkg_name, expected_dir):
    written = write_skeleton("demo", kind="python", pkg_name=bad_pkg_name, repo_name="demo")

    assert expected_dir in written
    # Every written path must land inside the validated tree — no traversal.
    for rel in written:
        resolved = (tree / rel).resolve()
        assert resolved.is_relative_to(tree.resolve())


def test_unsalvageable_pkg_name_raises_value_error(tree):
    with pytest.raises(ValueError):
        write_skeleton("demo", kind="python", pkg_name="///", repo_name="demo")


def test_scaffold_writer_imports_no_subprocess_and_no_keyring():
    import ast

    module_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/loop_engine/tools/scaffold/writer.py"
    )
    tree_ast = ast.parse(module_path.read_text())
    for node in ast.walk(tree_ast):
        if isinstance(node, ast.Import):
            names = {alias.name for alias in node.names}
            assert "subprocess" not in names
            assert "keyring" not in names
        if isinstance(node, ast.ImportFrom):
            assert node.module not in {"subprocess", "keyring"}
