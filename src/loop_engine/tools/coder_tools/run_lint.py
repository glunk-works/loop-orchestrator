"""Run ruff (check + format --check) against a path inside the run's artifact tree.

The fifth sanctioned subprocess surface, alongside run_tests' pytest.
Containment mirrors run_tests exactly: fixed argv (`sys.executable -m ruff
...`), shell never used, a hard timeout, output size-capped, target path
validated with the same traversal rules as every other tool. Unlike
run_tests, `ruff check` / `ruff format --check` statically parse the target
files -- they never execute model-generated code, so this surface is
strictly lower-risk than the one it sits beside.
"""

import subprocess
import sys

from loop_engine.tools.coder_tools import resolve_tool_path, truncate_result

LINT_TIMEOUT_SECONDS = 60

RUN_LINT_TOOL_SCHEMA: dict = {
    "name": "run_lint",
    "description": (
        "Run `ruff check` and `ruff format --check` against a file or "
        "directory in the run's artifact tree (e.g. src/). Use it to verify "
        "your implementation before claiming any 'ruff clean' acceptance "
        "criterion is met."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative file or directory, e.g. src"}
        },
        "required": ["path"],
    },
}


def run_ruff(path: str) -> tuple[int, str]:
    """Execute `ruff check` + `ruff format --check` on a validated path.

    Returns (exit_code, capped output); exit_code is nonzero if either check
    reports a finding. Structured entry point shared by the run_lint tool.
    """
    target = resolve_tool_path(path)
    check = subprocess.run(  # noqa: S603 — fixed argv on a traversal-validated path, no shell; ruff statically parses the target, never executes it
        [sys.executable, "-m", "ruff", "check", str(target)],
        capture_output=True,
        text=True,
        timeout=LINT_TIMEOUT_SECONDS,
    )
    fmt = subprocess.run(  # noqa: S603 — see above
        [sys.executable, "-m", "ruff", "format", "--check", str(target)],
        capture_output=True,
        text=True,
        timeout=LINT_TIMEOUT_SECONDS,
    )
    exit_code = check.returncode or fmt.returncode
    output = truncate_result(
        f"ruff check:\n{check.stdout}{check.stderr}\n\n"
        f"ruff format --check:\n{fmt.stdout}{fmt.stderr}".strip()
    )
    return exit_code, output


def format_run_lint_result(exit_code: int, output: str) -> str:
    """Format a (exit_code, output) pair into the run_lint tool's result string.

    Single source of truth for the result shape shared with
    `parse_run_lint_result` so producer and consumer never drift.
    """
    return f"ruff exit code: {exit_code}\n\n{output}"


def parse_run_lint_result(text: str) -> tuple[int, str]:
    """Recover (exit_code, output) from a `format_run_lint_result` string.

    Splits on the first blank line only, so multi-line/blank-line output
    round-trips intact.
    """
    header, output = text.split("\n\n", 1)
    exit_code = int(header.removeprefix("ruff exit code: "))
    return exit_code, output


def run_lint(path: str) -> str:
    """Tool-facing wrapper: ruff result formatted for the model."""
    exit_code, output = run_ruff(path)
    return format_run_lint_result(exit_code, output)
