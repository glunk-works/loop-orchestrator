import subprocess
from pathlib import Path

import pytest

from loop_engine.tools.coder_tools import grep, list_files, read_file
from loop_engine.tools.coder_tools.run_tests import run_pytest, run_tests


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("def foo():\n    return 42\n")
    (tmp_path / "sprints" / "01_foo").mkdir(parents=True)
    (tmp_path / "sprints" / "01_foo" / "plan.md").write_text("Sprint one plan.\n")


# --- traversal rejection: every tool refuses model-controlled escapes -------


@pytest.mark.parametrize(
    "bad_path",
    ["../etc/passwd", "/etc/passwd", "src/../../etc/passwd", "state/run-1/snapshot.json"],
)
def test_read_file_rejects_escaping_or_disallowed_paths(bad_path) -> None:
    with pytest.raises(ValueError):
        read_file(bad_path)


@pytest.mark.parametrize("bad_path", ["../", "/", "src/.."])
def test_list_files_rejects_escaping_paths(bad_path) -> None:
    with pytest.raises(ValueError):
        list_files(bad_path)


@pytest.mark.parametrize("bad_path", ["../etc", "/etc"])
def test_grep_rejects_escaping_paths(bad_path) -> None:
    with pytest.raises(ValueError):
        grep("x", bad_path)


def test_read_file_rejects_symlink_escape(tmp_path) -> None:
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("secret")
    (tmp_path / "src" / "link.txt").symlink_to(outside)

    with pytest.raises(ValueError):
        read_file("src/link.txt")


def test_run_tests_rejects_escaping_paths() -> None:
    with pytest.raises(ValueError):
        run_tests("../somewhere")


# --- happy paths -------------------------------------------------------------


def test_read_file_returns_contents() -> None:
    assert "return 42" in read_file("src/foo.py")


def test_read_file_missing_file_raises() -> None:
    with pytest.raises(ValueError, match="No such file"):
        read_file("src/missing.py")


def test_list_files_lists_recursively() -> None:
    listing = list_files("sprints")
    assert str(Path("sprints") / "01_foo" / "plan.md") in listing


def test_grep_returns_path_line_matches() -> None:
    result = grep(r"return \d+", "src")
    assert "src" in result
    assert ":2:" in result
    assert "return 42" in result


def test_grep_reports_no_matches() -> None:
    assert grep("nonexistent_symbol", "src") == "(no matches)"


# --- run_tests ----------------------------------------------------------------


def test_run_pytest_passes_on_green_tree() -> None:
    Path("src/test_green.py").write_text("def test_ok():\n    assert True\n")

    exit_code, output = run_pytest("src")

    assert exit_code == 0
    assert "1 passed" in output


def test_run_pytest_fails_on_red_tree_with_output_captured() -> None:
    Path("src/test_red.py").write_text("def test_broken():\n    assert 1 == 2\n")

    exit_code, output = run_pytest("src")

    assert exit_code != 0
    assert "test_broken" in output


def test_run_pytest_reports_exit_5_when_no_tests_collected() -> None:
    exit_code, _output = run_pytest("src/foo.py")

    assert exit_code == 5


def test_run_tests_tool_output_names_the_exit_code() -> None:
    Path("src/test_green.py").write_text("def test_ok():\n    assert True\n")

    result = run_tests("src")

    assert result.startswith("pytest exit code: 0")


def test_run_pytest_enforces_timeout(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.TimeoutExpired):
        run_pytest("src")


def test_run_pytest_truncates_oversized_output(monkeypatch) -> None:
    class FakeCompleted:
        returncode = 1
        stdout = "x" * 100_000
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeCompleted())

    _exit_code, output = run_pytest("src")

    assert len(output) < 100_000
    assert output.endswith("[truncated]")
