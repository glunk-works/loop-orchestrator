"""The sprint-block output adapter: parse `### FILEPATH:` blocks, write each
sprint file, emit `sprint_plans` + `task_manifest`, capture Open Questions.

This is the tail of what the classic `AgileSprintBreakdownPersona.run` did.
Phase 6 deleted that class, but the behavior survives in
`declarative/services.finalize_sprint_blocks` (over the same
`_parse_sprint_blocks` parser, which is why the output stayed byte-identical),
so these assertions are ported from that persona's own tests rather than lost
with it.
"""

import json
from pathlib import Path

import pytest

from loop_engine.core.state import State
from loop_engine.personas.agile_sprint_breakdown.persona import _parse_sprint_blocks
from loop_engine.personas.declarative import services

TWO_SPRINTS = """### FILEPATH: /sprints/01_foo/sprint_plan.md

**Sprint Goal:** Foo.

---

### FILEPATH: /sprints/02_bar/sprint_plan.md

**Sprint Goal:** Bar.
"""


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state() -> State:
    return State(
        schema_version=3,
        run_id="run-1",
        stage_history=[],
        artifacts={"architecture_definition": "# Architecture"},
    )


def _finalize(text: str, state: State | None = None) -> State:
    return services.finalize_sprint_blocks(
        produces="sprint_plans",
        effective_text=text,
        raw_response=text,
        stage_name="SprintBreakdownGenerator",
        state=state or _state(),
    )


def test_parses_two_sprint_blocks_and_strips_the_divider() -> None:
    blocks = _parse_sprint_blocks(TWO_SPRINTS)

    assert [b["path"] for b in blocks] == [
        "/sprints/01_foo/sprint_plan.md",
        "/sprints/02_bar/sprint_plan.md",
    ]
    # The "---" between blocks is response framing, not file content.
    assert blocks[0]["content"] == "**Sprint Goal:** Foo."
    assert blocks[1]["content"] == "**Sprint Goal:** Bar."


def test_writes_a_sprint_plan_file_per_block() -> None:
    result = _finalize(TWO_SPRINTS)

    assert Path("sprints/01_foo/sprint_plan.md").read_text() == "**Sprint Goal:** Foo."
    assert Path("sprints/02_bar/sprint_plan.md").read_text() == "**Sprint Goal:** Bar."
    assert len(json.loads(result.artifacts["sprint_plans"])) == 2
    # A manifest is always emitted (these fixture sprints declare no **Tasks:**,
    # so it is legitimately empty — manifest extraction itself is covered by
    # tests/personas/test_task_manifest.py).
    assert json.loads(result.artifacts["task_manifest"]) == []


def test_skips_an_invalid_path_without_crashing_the_stage() -> None:
    # A model-supplied path that escapes the artifact tree must be dropped, not
    # written and not fatal — the other sprints still land.
    text = TWO_SPRINTS + "\n### FILEPATH: ../../etc/passwd\n\npwned\n"

    result = _finalize(text)

    assert not Path("../../etc/passwd").exists()
    assert Path("sprints/01_foo/sprint_plan.md").is_file()
    # The block is still reported in sprint_plans; only the *write* is refused.
    assert len(json.loads(result.artifacts["sprint_plans"])) == 3


def test_captures_open_questions_from_the_raw_response() -> None:
    text = TWO_SPRINTS + "\n## Open Questions\n\n- Which cloud region?\n"

    result = services.finalize_sprint_blocks(
        produces="sprint_plans",
        effective_text=TWO_SPRINTS,
        raw_response=text,
        stage_name="SprintBreakdownGenerator",
        state=_state(),
    )

    assert [q.text for q in result.questions] == ["Which cloud region?"]
    assert result.questions[0].origin_stage == "SprintBreakdownGenerator"
