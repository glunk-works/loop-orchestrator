"""Run pytest against a path inside the run's artifact tree.

This is the system's only subprocess surface besides issue_io's `gh`, and
its first execution of model-influenced input. Containment: fixed argv
(`sys.executable -m pytest <validated path>`), shell never used, a hard
timeout, output size-capped before it re-enters the model's context, and the
target path validated with the same traversal rules as every other tool.
The operating assumption is the sandboxed devcontainer — generated code runs
with the invoking user's privileges (see docs/architecture_definition.md).
"""

import subprocess
import sys

from loop_orchestrator.tools.coder_tools import resolve_tool_path, truncate_result

TEST_TIMEOUT_SECONDS = 120

# pytest exit code 5: no tests were collected.
PYTEST_NO_TESTS_COLLECTED = 5


def run_pytest(path: str) -> tuple[int, str]:
    """Execute pytest on a validated path; returns (exit_code, capped output).

    Structured entry point shared by the run_tests tool and the Coder
    stage's evidence gate.
    """
    target = resolve_tool_path(path)
    completed = subprocess.run(  # noqa: S603 — fixed argv on a traversal-validated path, no shell; executes model-generated tests by design, inside the sandboxed devcontainer
        [sys.executable, "-m", "pytest", str(target)],
        capture_output=True,
        text=True,
        timeout=TEST_TIMEOUT_SECONDS,
    )
    output = truncate_result(f"{completed.stdout}\n{completed.stderr}".strip())
    return completed.returncode, output


def format_run_tests_result(exit_code: int, output: str) -> str:
    """Format a (exit_code, output) pair into the run_tests tool's result string.

    Single source of truth for the result shape shared with
    `parse_run_tests_result` so producer and consumer never drift.
    """
    return f"pytest exit code: {exit_code}\n\n{output}"


def parse_run_tests_result(text: str) -> tuple[int, str]:
    """Recover (exit_code, output) from a `format_run_tests_result` string.

    Splits on the first blank line only, so multi-line/blank-line output
    (including output that itself contains "pytest exit code:"-like text)
    round-trips intact.
    """
    header, output = text.split("\n\n", 1)
    exit_code = int(header.removeprefix("pytest exit code: "))
    return exit_code, output


def run_tests(path: str) -> str:
    """Tool-facing wrapper: pytest result formatted for the model."""
    exit_code, output = run_pytest(path)
    return format_run_tests_result(exit_code, output)
