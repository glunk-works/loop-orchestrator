import re
from pathlib import Path

from loop_engine.personas.agile_sprint_breakdown.persona import (
    PROMPT_TEMPLATE as SPRINT_BREAKDOWN_TEMPLATE,
)
from loop_engine.personas.architecture.persona import PROMPT_TEMPLATE as ARCHITECTURE_TEMPLATE
from loop_engine.personas.coder_iac.persona import PROMPT_TEMPLATE as CODER_IAC_TEMPLATE
from loop_engine.personas.pm.persona import PROMPT_TEMPLATE as PM_TEMPLATE

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"
_HEADER_RE = re.compile(r"^#{1,6} .+$", re.MULTILINE)


def _headers(text: str) -> list[str]:
    return _HEADER_RE.findall(text)


def test_architecture_prompt_matches_source_headers() -> None:
    source = (PROMPTS_DIR / "02_architecture_definition_prompt.md").read_text()
    for header in _headers(source):
        assert header in ARCHITECTURE_TEMPLATE


def test_agile_sprint_breakdown_prompt_matches_source_headers() -> None:
    source = (PROMPTS_DIR / "03_agile_sprint_breakdown_prompt.md").read_text()
    for header in _headers(source):
        assert header in SPRINT_BREAKDOWN_TEMPLATE

    # Explicit check against the example given in the sprint plan.
    assert "## ROLE" in SPRINT_BREAKDOWN_TEMPLATE
    assert "## OBJECTIVE" in SPRINT_BREAKDOWN_TEMPLATE
    assert "## TASK INSTRUCTIONS" in SPRINT_BREAKDOWN_TEMPLATE


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


def test_pm_prompt_matches_pm_agent_loop_source_phrasing() -> None:
    # No prompts/0N_*.md source exists for PM: pm-agent-loop's own PM
    # interview was never captured as a standalone markdown prompt file (it
    # produced this very repo's docs/project_spec.json directly). Per the
    # project owner's direction, PMPersona.PROMPT_TEMPLATE is ported from
    # pm-agent-loop's src/pm_agent_loop/personas/pm.py
    # (_ARTIFACT_EXTRACTION_SYSTEM_PROMPT_TEMPLATE) instead of a prompts/
    # file, so this pins the ported phrasing rather than diffing a file.
    expected_phrases = [
        "You are the PM persona extracting candidate answers",
        "<untrusted_artifact>",
        "Do not guess, infer beyond what is written, or invent an answer",
        "Respond with ONLY a single JSON object",
    ]
    for phrase in expected_phrases:
        assert phrase in PM_TEMPLATE
