"""The prompt files ARE the source of truth the generator nodes load.

Until Phase 6 these asserted the on-disk prompt files were byte-identical to the
classic personas' embedded templates — the parity guarantee that made swapping in
the declarative nodes safe. With the classic personas deleted there is no second
copy to diff against; `prompts/` is now the only source, so what is worth pinning
is that every bundled config resolves to a real prompt file carrying the section
headers its output adapter depends on.
"""

import pytest

from loop_engine.personas.declarative.config import (
    load_named_config,
    load_prompt,
    resolve_prompt_path,
)

# The markers each persona's prompt must carry for its adapter to work: section
# headers the model is told to emit, or (for PM, which has no headers) the
# preamble phrase that defines the extraction task.
MANDATED_MARKERS = {
    "architecture": ["## Output Requirements"],
    "sprint_breakdown": ["## ROLE", "## OBJECTIVE", "## TASK INSTRUCTIONS"],
    "pm": ["extracting candidate answers"],
}


@pytest.mark.parametrize("name", sorted(MANDATED_MARKERS))
def test_each_config_points_at_an_existing_prompt_with_its_mandated_markers(name) -> None:
    cfg = load_named_config(name)

    assert resolve_prompt_path(cfg.prompt_file).is_file()
    body = load_prompt(cfg.prompt_file)
    for marker in MANDATED_MARKERS[name]:
        assert marker in body, f"{name}: missing {marker!r}"


@pytest.mark.parametrize("name", sorted(MANDATED_MARKERS))
def test_each_configs_revision_prompt_file_exists_when_declared(name) -> None:
    cfg = load_named_config(name)

    if cfg.revision_feedback_prompt_file is not None:
        assert resolve_prompt_path(cfg.revision_feedback_prompt_file).is_file()
