"""GitHub Issues transport for the human end of the escalation ladder.

This module is the only place in the codebase that talks to GitHub, mirroring
how tools/state_io is the only filesystem writer. It shells out to `gh`
(already authenticated in the devcontainer) rather than embedding a token —
no credential ever passes through this process's own configuration.

Answer convention (documented in the issue body it files): the human replies
with a single comment containing a fenced ```answers block, one `N: answer`
line per question number. Closing the issue without such a comment aborts
the run.
"""

import json
import re
import subprocess

from loop_engine.core.state import IssueRef, Question, State

ISSUE_LABEL = "loop-engine/needs-human"

_ANSWERS_BLOCK_RE = re.compile(r"```answers\s*\n(.*?)```", re.DOTALL)
_ANSWER_LINE_RE = re.compile(r"^\s*(\d+)\s*[:.)]\s*(.+?)\s*$")


class IssueClosedWithoutAnswersError(Exception):
    pass


def _run_gh(args: list[str]) -> str:
    result = subprocess.run(  # noqa: S603 -- fixed executable, no shell, args are not attacker-controlled strings
        ["gh", *args],  # noqa: S607 -- resolved via PATH intentionally: gh's install location varies by platform
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return result.stdout


def _issue_body(state: State, questions: list[Question], snapshot_path: str) -> str:
    lines = [
        f"loop-engine run `{state.run_id}` is paused: the persona pipeline has "
        "questions no automated layer could resolve.",
        "",
        f"Snapshot: `{snapshot_path}`",
        "",
        "## Questions",
        "",
    ]
    for number, question in enumerate(questions, start=1):
        lines.append(f"{number}. **[{question.origin_stage}]** {question.text}")
    lines += [
        "",
        "## How to answer",
        "",
        "Reply with a single comment containing a fenced block, one line per",
        "question number:",
        "",
        "````",
        "```answers",
        "1: your answer",
        "2: your answer",
        "```",
        "````",
        "",
        "Then run `loop-engine resume --from-issue <this issue number>`.",
        "Closing this issue without an answers comment aborts the run.",
    ]
    return "\n".join(lines)


def file_question_issue(state: State, questions: list[Question], snapshot_path: str) -> IssueRef:
    title = f"loop-engine: {len(questions)} question(s) for run {state.run_id}"
    url = _run_gh(
        [
            "issue",
            "create",
            "--title",
            title,
            "--body",
            _issue_body(state, questions, snapshot_path),
            "--label",
            ISSUE_LABEL,
        ]
    ).strip()
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    return IssueRef(number=number, url=url)


def read_issue(issue_number: int) -> dict:
    raw = _run_gh(
        [
            "issue",
            "view",
            str(issue_number),
            "--json",
            "state,body,comments",
        ]
    )
    return json.loads(raw)


def parse_snapshot_path(issue_data: dict) -> str | None:
    match = re.search(r"^Snapshot: `([^`]+)`", issue_data.get("body", ""), re.MULTILINE)
    return match.group(1) if match else None


def read_issue_answers(issue_number: int, issue_data: dict | None = None) -> dict[int, str]:
    """Return {question number: answer} from the issue's latest answers comment.

    Raises IssueClosedWithoutAnswersError if the issue is closed with no
    parseable answers — the human's signal to abort the run.
    """
    data = issue_data if issue_data is not None else read_issue(issue_number)

    answers: dict[int, str] = {}
    for comment in data.get("comments", []):
        block = _ANSWERS_BLOCK_RE.search(comment.get("body", ""))
        if block is None:
            continue
        parsed: dict[int, str] = {}
        for line in block.group(1).splitlines():
            match = _ANSWER_LINE_RE.match(line)
            if match:
                parsed[int(match.group(1))] = match.group(2)
        if parsed:
            answers = parsed  # later comments supersede earlier ones

    if not answers and data.get("state") == "CLOSED":
        raise IssueClosedWithoutAnswersError(
            f"Issue #{issue_number} was closed without an answers comment; "
            "treating the run as aborted by the human."
        )
    return answers


def apply_answers_to_questions(
    questions: list[Question],
    filed_questions: list[Question],
    answers: dict[int, str],
    issue_number: int,
) -> list[Question]:
    """Mark filed questions resolved from the human's numbered answers.

    `filed_questions` preserves the numbering used in the issue body; answers
    referencing numbers outside it are ignored.
    """
    resolution_by_id = {
        filed_questions[number - 1].id: text
        for number, text in answers.items()
        if 1 <= number <= len(filed_questions)
    }
    return [
        q.model_copy(
            update={
                "resolution": resolution_by_id[q.id],
                "resolved_by": f"human:{issue_number}",
            }
        )
        if q.id in resolution_by_id and q.resolution is None
        else q
        for q in questions
    ]
