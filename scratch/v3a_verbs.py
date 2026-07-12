"""V3a — verb-level issue round-trip against the REAL issue MCP server and REAL gh.

No LLM. No budget. Clears DEFERRED_VERIFICATION.md §9 bullets 1-3.

    cd "$SCRATCH_CLONE"
    hatch run python /workspace/scratch/v3a_verbs.py

MUST be run with cwd inside the disposable scratch clone: `create_issue` shells
`gh issue create` with no `--repo`, so `gh` resolves the target repo from the cwd's
git remote, and the issue server inherits this process's cwd (`"cwd": null` in
loop_engine.mcp.json). Run from /workspace and you file on glunk-works/loop-engine
for real -- which is how issues #16/#19/#21 got there. Step 0 refuses to proceed
unless cwd resolves to a repo that is NOT loop-engine.

Evidence lands in ./v3a_evidence/ (relative to cwd, i.e. inside the scratch clone).
"""

import json
import subprocess
import sys
from pathlib import Path

from loop_engine.core.gates import new_question
from loop_engine.core.state import CURRENT_SCHEMA_VERSION, State
from loop_engine.tools.issue_io import github as classic
from loop_engine.tools.issue_io.mcp_client import mcp_issue_filer, mcp_issue_reader
from loop_engine.tools.mcp.provider import build_issue_provider

EVIDENCE = Path("v3a_evidence")
LABEL = classic.ISSUE_LABEL
ANSWERS_COMMENT = "```answers\n1: use PostgreSQL\n2: 90 days\n```"


def gh(args: list[str]) -> str:
    return subprocess.run(  # noqa: S603 -- fixed executable, no shell, args not attacker-controlled
        ["gh", *args],  # noqa: S607 -- resolved via PATH intentionally, as tools/issue_io does
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout


def record(name: str, payload) -> None:
    EVIDENCE.mkdir(exist_ok=True)
    body = payload if isinstance(payload, str) else json.dumps(payload, indent=2, sort_keys=True)
    (EVIDENCE / name).write_text(body)


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


# --- Step 0: B1 guard + B3 provider-launch smoke ------------------------------


def step0_guard_and_launch(provider) -> None:
    print("\n[V3a.0] B1 cwd guard + B3 provider launch")

    target = json.loads(gh(["repo", "view", "--json", "nameWithOwner"]))["nameWithOwner"]
    print(f"  cwd resolves to: {target}")
    if target.endswith("/loop-engine"):
        fail(
            f"cwd resolves to {target} -- refusing. V3 must run from a disposable "
            "scratch clone, or it files real escalation issues on the project repo (B1)."
        )
    record("00_target_repo.txt", target)
    ok(f"target repo is a scratch repo ({target}), not loop-engine")

    names = sorted(t["name"] for t in provider.tools)
    print(f"  discovered tools: {names}")
    if names != ["create_issue", "read_issue"]:
        fail(f"expected exactly ['create_issue', 'read_issue'], got {names}")
    record("00_tools.json", names)
    ok("issue server launched; exposes exactly {create_issue, read_issue}")

    labels = json.loads(gh(["label", "list", "--json", "name"]))
    if not any(label["name"] == LABEL for label in labels):
        fail(
            f"label {LABEL!r} does not exist in {target} -- `gh issue create --label` will "
            f"fail hard (B2). Create it:\n"
            f"    gh label create '{LABEL}' --color d73a4a"
        )
    ok(f"label {LABEL!r} exists")


# --- Step 1: real create_issue through the server -----------------------------


def step1_create(provider) -> int:
    print("\n[V3a.1] real create_issue through the MCP server")

    raw = provider.execute(
        "create_issue",
        {
            "title": "V3a: create_issue through the issue MCP server",
            "body": "Throwaway issue filed by the V3a verb round-trip. Safe to delete.",
            "label": LABEL,
        },
    )
    ref = json.loads(raw)
    number, url = ref["number"], ref["url"]
    print(f"  filed: #{number} {url}")
    record("01_create_issue_ref.json", ref)

    view = json.loads(gh(["issue", "view", str(number), "--json", "number,labels,state,url"]))
    if view["number"] != number:
        fail(f"IssueRef number {number} != gh's {view['number']}")
    if LABEL not in [label["name"] for label in view["labels"]]:
        fail(f"issue #{number} does not carry the {LABEL!r} label")
    record("01_gh_view.json", view)
    ok(f"real issue #{number} exists and carries {LABEL!r}")
    return number


# --- Step 2: real read_issue through the server, vs gh directly ----------------


def step2_read(provider, number: int) -> None:
    print("\n[V3a.2] real read_issue through the MCP server, compared to gh directly")

    gh(["issue", "comment", str(number), "--body", ANSWERS_COMMENT])
    print(f"  posted an ```answers comment on #{number}")

    via_mcp = mcp_issue_reader(provider)(number)
    via_gh = json.loads(gh(["issue", "view", str(number), "--json", "state,body,comments"]))

    record("02_read_via_mcp.json", via_mcp)
    record("02_read_via_gh.json", via_gh)

    # THE §9 bullet: the server must round-trip gh's JSON faithfully, not just the
    # monkeypatched shape the hermetic unit tests assert.
    if via_mcp != via_gh:
        fail(
            "read_issue through MCP != `gh issue view` directly. Diff the two evidence "
            "files -- the server is not round-tripping gh's JSON faithfully."
        )
    ok("read_issue via MCP is byte-identical to `gh issue view --json state,body,comments`")

    answers = classic.parse_issue_answers(via_mcp)
    if answers != {1: "use PostgreSQL", 2: "90 days"}:
        fail(f"answers parsed from the MCP read are wrong: {answers}")
    ok(f"answers parse out of the MCP-read payload: {answers}")


# --- Step 3: adapters (mcp_issue_filer / mcp_issue_reader) vs classic ----------


def step3_adapters(provider) -> None:
    print("\n[V3a.3] mcp_issue_filer / mcp_issue_reader vs the raw gh primitives")

    state = State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id="v3a" + "0" * 29,
        stage_history=[],
        artifacts={"human_input": "V3a adapter round-trip"},
    )
    questions = [
        new_question("PMGenerator", "Which datastore should the service use?"),
        new_question("PMGenerator", "What is the data retention window?"),
    ]
    snapshot_hint = f"state/{state.run_id}/00_awaiting_issue.json"

    mcp_ref = mcp_issue_filer(provider)(state, questions, snapshot_hint)
    classic_ref = classic.create_issue(
        *classic.render_question_issue(state, questions, snapshot_hint)
    )
    print(f"  MCP-filed:     #{mcp_ref.number} {mcp_ref.url}")
    print(f"  classic-filed: #{classic_ref.number} {classic_ref.url}")
    record("03_mcp_ref.json", mcp_ref.model_dump())
    record("03_classic_ref.json", classic_ref.model_dump())

    # The issues are distinct, so compare structurally: same rendered body/title/label,
    # and the IssueRef shape agrees (number parsed out of the URL).
    mcp_view = json.loads(gh(["issue", "view", str(mcp_ref.number), "--json", "title,body,labels"]))
    classic_view = json.loads(
        gh(["issue", "view", str(classic_ref.number), "--json", "title,body,labels"])
    )
    record("03_mcp_view.json", mcp_view)
    record("03_classic_view.json", classic_view)

    if mcp_view != classic_view:
        fail("the MCP-filed issue and the classic-filed issue differ in title/body/labels")
    ok("MCP-filed issue is identical in title/body/labels to the classic-filed one")

    for ref in (mcp_ref, classic_ref):
        if not ref.url.rstrip("/").endswith(str(ref.number)):
            fail(f"IssueRef {ref} number/url disagree")
    ok("IssueRef number/url agree on both paths")

    # And the read adapter agrees with the classic reader on the SAME issue.
    gh(["issue", "comment", str(mcp_ref.number), "--body", ANSWERS_COMMENT])
    via_mcp = classic.parse_issue_answers(mcp_issue_reader(provider)(mcp_ref.number))
    via_classic = classic.parse_issue_answers(classic.read_issue(mcp_ref.number))
    if via_mcp != via_classic:
        fail(f"answers disagree: MCP {via_mcp} vs classic {via_classic}")
    record("03_answers.json", {"via_mcp": via_mcp, "via_classic": via_classic})
    ok(f"mcp_issue_reader and the raw gh read agree on the same issue: {via_mcp}")


def main() -> None:
    print("V3a -- verb-level issue round-trip (real server, real gh, no LLM)")
    with build_issue_provider() as provider:
        step0_guard_and_launch(provider)
        number = step1_create(provider)
        step2_read(provider, number)
        step3_adapters(provider)

    print("\nV3a PASS -- evidence in ./v3a_evidence/")
    print("§9 bullets 1-3 cleared. Proceed to V3b (v3b_engine.py).")


if __name__ == "__main__":
    main()
