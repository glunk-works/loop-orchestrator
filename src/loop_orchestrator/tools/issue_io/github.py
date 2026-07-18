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

from loop_orchestrator.core.state import IssueRef, Question, State

ISSUE_LABEL = "loop-orchestrator/needs-human"

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
        f"loop-orchestrator run `{state.run_id}` is paused: the persona pipeline has "
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
        "Then run `loop-orchestrator resume --from-issue <this issue number>`.",
        "Closing this issue without an answers comment aborts the run.",
    ]
    return "\n".join(lines)


def render_question_issue(
    state: State, questions: list[Question], snapshot_path: str
) -> tuple[str, str, str]:
    """Pure: the (title, body, label) an issue-filing call needs. No `gh`."""
    title = f"loop-orchestrator: {len(questions)} question(s) for run {state.run_id}"
    return title, _issue_body(state, questions, snapshot_path), ISSUE_LABEL


def create_issue(title: str, body: str, label: str, *, repo: str | None = None) -> IssueRef:
    """The one `gh`-write primitive: shells `gh issue create` and parses the
    resulting URL into an `IssueRef`. Takes only strings, so this is the verb
    an MCP boundary can carry without a rich domain object crossing it.
    `repo` (owner/repo), when given, is passed as `--repo` — an explicit
    destination instead of `gh`'s implicit cwd-derived resolution (R8)."""
    args = ["issue", "create", "--title", title, "--body", body, "--label", label]
    if repo is not None:
        args += ["--repo", repo]
    url = _run_gh(args).strip()
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    return IssueRef(number=number, url=url)


def read_issue(issue_number: int, *, repo: str | None = None) -> dict:
    """Shells `gh issue view`. `repo` (owner/repo), when given, is passed as
    `--repo` — see `create_issue` for why an explicit destination matters."""
    # `url` identifies which repo the issue actually came from, so a resume can
    # verify it read the issue it meant to rather than a same-numbered issue in
    # whatever repo the CWD happened to resolve to.
    args = ["issue", "view", str(issue_number), "--json", "state,body,comments,url"]
    if repo is not None:
        args += ["--repo", repo]
    raw = _run_gh(args)
    return json.loads(raw)


def parse_snapshot_path(issue_data: dict) -> str | None:
    match = re.search(r"^Snapshot: `([^`]+)`", issue_data.get("body", ""), re.MULTILINE)
    return match.group(1) if match else None


_ISSUE_URL_RE = re.compile(r"^https://github\.com/([^/]+/[^/]+)/issues/\d+/?$")


def repo_from_issue_url(url: str) -> str:
    """The `owner/repo` slug a canonical GitHub issue URL
    (`https://github.com/owner/repo/issues/N`) belongs to.

    F1a: makes `resume --snapshot` unambiguous. A snapshot's own
    `pending_issue.url` is the only first-hand record of where its escalation
    was actually filed, recorded at pause time by the process that filed it
    -- so deriving the read repo from it (rather than CWD or a guess) is what
    closes the destination ambiguity CWD-based resolution cannot.
    """
    match = _ISSUE_URL_RE.match(url)
    if not match:
        raise ValueError(f"Not a recognizable GitHub issue URL: {url!r}")
    return match.group(1)


def parse_issue_answers(issue_data: dict, issue_number: int | None = None) -> dict[int, str]:
    """Pure: {question number: answer} from an already-fetched issue view's
    latest answers block. No `gh`.

    Scans every ```answers block in every comment via `finditer` (not just
    the first block per comment): a human "Quote reply" that echoes the
    bot's own example block would otherwise shadow the real answers below it
    (R6). Later blocks — whether later in the same comment or in a later
    comment — supersede earlier ones.

    Raises IssueClosedWithoutAnswersError if the issue is closed with no
    parseable answers — the human's signal to abort the run. `issue_number`,
    when given, is folded into that error's message (R5).
    """
    answers: dict[int, str] = {}
    for comment in issue_data.get("comments", []):
        for block in _ANSWERS_BLOCK_RE.finditer(comment.get("body", "")):
            parsed: dict[int, str] = {}
            for line in block.group(1).splitlines():
                match = _ANSWER_LINE_RE.match(line)
                if match:
                    parsed[int(match.group(1))] = match.group(2)
            if parsed:
                answers = parsed  # later blocks supersede earlier ones

    if not answers and issue_data.get("state") == "CLOSED":
        ref = f" #{issue_number}" if issue_number is not None else ""
        raise IssueClosedWithoutAnswersError(
            f"Issue{ref} was closed without an answers comment; "
            "treating the run as aborted by the human."
        )
    return answers
