"""Prompt-content guardrails.

Until Phase 6 this file diffed each persona's *embedded* PROMPT_TEMPLATE against
its `prompts/*.md` source file — a drift check between two copies. The classic
document personas (and their embedded templates) are now deleted, so for PM,
Architecture and Sprint Breakdown there is no second copy to diff: `prompts/` is
the sole source of truth, and `tests/personas/declarative/test_config_prompts.py`
asserts each generator config points at a real prompt file with its mandated
headers.

What remains here are the guardrails that still have a live subject:

- The **Coder** prompt is still embedded (`personas/coder_iac/shared.py`), shared
  by the Ralph coder, so its `prompts/04_*.md` drift check stands.
- The Coder prompt's sprint-30 test-scope directives (F-RALPH-OVERSPEC-TEST) —
  a regression guardrail, pinned by content rather than by diff.
- The PM prompt's ported phrasing, re-pointed at the `prompts/` file now that
  the embedded template is gone.
"""

import re
from pathlib import Path

from loop_engine.personas.coder_iac.shared import PROMPT_TEMPLATE as CODER_IAC_TEMPLATE

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"
_HEADER_RE = re.compile(r"^#{1,6} .+$", re.MULTILINE)


def _headers(text: str) -> list[str]:
    return _HEADER_RE.findall(text)


def test_coder_iac_prompt_matches_source_headers() -> None:
    source = (PROMPTS_DIR / "04_developer_iac_implementation_prompt.md").read_text()
    for header in _headers(source):
        assert header in CODER_IAC_TEMPLATE


def test_coder_iac_prompt_carries_test_scope_guardrail() -> None:
    # sprint 30 (F-RALPH-OVERSPEC-TEST): tests must cover exactly the enumerated
    # acceptance criteria, never private internals or import mechanics.
    assert "private or underscore-prefixed module" in CODER_IAC_TEMPLATE
    assert "do not add tests for behavior" in CODER_IAC_TEMPLATE
    # Preexisting directives untouched by the new bullet.
    assert "Implement only the sprint provided in this invocation." in CODER_IAC_TEMPLATE
    assert "No ambiguity resolution by assumption." in CODER_IAC_TEMPLATE
    assert "Enforce the Global Definition of Done" in CODER_IAC_TEMPLATE
    assert "no secret or\ncredential value appears anywhere in the output" in CODER_IAC_TEMPLATE


def test_pm_prompt_keeps_the_pm_agent_loop_source_phrasing() -> None:
    # The PM extraction prompt is ported from pm-agent-loop's
    # src/pm_agent_loop/personas/pm.py (_ARTIFACT_EXTRACTION_SYSTEM_PROMPT_TEMPLATE),
    # per the project owner's direction to mirror that tool's PM logic rather than
    # invent prompt content with no source to check for drift. Phase 6 deleted the
    # embedded copy, so this now pins the phrasing in the prompts/ file itself —
    # the file the PM generator config actually loads.
    body = (PROMPTS_DIR / "00_pm_extraction_prompt.md").read_text()
    expected_phrases = [
        "You are the PM persona extracting candidate answers",
        "<untrusted_artifact>",
        "Do not guess, infer beyond what is written, or invent an answer",
        "Respond with ONLY a single JSON object",
    ]
    for phrase in expected_phrases:
        assert phrase in body
