"""The declarative prompt files ARE the source of truth the nodes load.

These invert the classic header-check parity test: rather than pinning an
embedded copy against a file, they assert the on-disk prompt files are
byte-identical to the personas' embedded templates (so a declarative node's
system_blocks equal the classic persona's), and that each bundled config points
at an existing prompt file carrying its mandated section headers.
"""

from loop_engine.personas.agile_sprint_breakdown.persona import (
    PROMPT_TEMPLATE as SPRINT_TEMPLATE,
)
from loop_engine.personas.architecture.persona import (
    PROMPT_TEMPLATE as ARCH_TEMPLATE,
)
from loop_engine.personas.architecture.persona import (
    RESOLUTION_PROMPT_TEMPLATE as ARCH_RES_TEMPLATE,
)
from loop_engine.personas.declarative.config import (
    load_named_config,
    load_prompt,
    resolve_prompt_path,
)
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS
from loop_engine.personas.pm.persona import (
    FOLLOWUP_PROMPT_TEMPLATE as PM_FOLLOWUP_TEMPLATE,
)
from loop_engine.personas.pm.persona import (
    PROMPT_TEMPLATE as PM_TEMPLATE,
)
from loop_engine.personas.pm.persona import (
    RESOLUTION_PROMPT_TEMPLATE as PM_RES_TEMPLATE,
)


def test_architecture_prompt_file_byte_identical_to_embedded() -> None:
    assert load_prompt("prompts/02_architecture_definition_prompt.md") == ARCH_TEMPLATE


def test_sprint_breakdown_prompt_file_byte_identical_to_embedded() -> None:
    assert load_prompt("prompts/03_agile_sprint_breakdown_prompt.md") == SPRINT_TEMPLATE


def test_pm_extraction_prompt_file_matches_formatted_embedded() -> None:
    expected = PM_TEMPLATE.format(fields=", ".join(CHECKLIST_FIELDS))
    assert load_prompt("prompts/00_pm_extraction_prompt.md") == expected


def test_pm_followup_prompt_file_byte_identical() -> None:
    assert load_prompt("prompts/00_pm_followup_prompt.md") == PM_FOLLOWUP_TEMPLATE


def test_resolution_prompt_files_byte_identical() -> None:
    assert load_prompt("prompts/00_pm_resolution_prompt.md") == PM_RES_TEMPLATE
    assert load_prompt("prompts/02_architecture_resolution_prompt.md") == ARCH_RES_TEMPLATE


def test_each_config_points_at_existing_prompt_with_headers() -> None:
    mandated = {
        "architecture": ["## Output Requirements"],
        "sprint_breakdown": ["## ROLE", "## OBJECTIVE", "## TASK INSTRUCTIONS"],
        "pm": ["extracting candidate answers"],  # PM preamble phrase (no headers)
    }
    for name, markers in mandated.items():
        cfg = load_named_config(name)
        assert resolve_prompt_path(cfg.prompt_file).is_file()
        body = load_prompt(cfg.prompt_file)
        for marker in markers:
            assert marker in body, f"{name}: missing {marker!r}"
