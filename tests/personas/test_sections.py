from loop_orchestrator.personas.sections import merge

PREVIOUS = """# Doc Title

Intro paragraph.

## Alpha

Original alpha body.

## Beta

Original beta body.

### FILEPATH: /sprints/01_foo/sprint_plan.md

Original sprint one.

## Gamma

Original gamma body.
"""


def test_merge_replaces_a_single_named_section() -> None:
    corrections = "## Beta\n\nCorrected beta body.\n"

    merged = merge(PREVIOUS, corrections)

    assert "Corrected beta body." in merged
    assert "Original beta body." not in merged
    # Everything else is byte-identical.
    assert "Original alpha body." in merged
    assert "Original gamma body." in merged
    assert "Original sprint one." in merged
    assert merged.startswith("# Doc Title\n\nIntro paragraph.\n")


def test_merge_replaces_multiple_sections_including_filepath_headers() -> None:
    corrections = (
        "## Alpha\n\nNew alpha.\n\n"
        "### FILEPATH: /sprints/01_foo/sprint_plan.md\n\nNew sprint one.\n"
    )

    merged = merge(PREVIOUS, corrections)

    assert "New alpha." in merged
    assert "New sprint one." in merged
    assert "Original alpha body." not in merged
    assert "Original sprint one." not in merged
    assert "Original beta body." in merged
    assert "Original gamma body." in merged


def test_merge_rejects_corrections_for_unknown_sections(caplog) -> None:
    corrections = "## Delta\n\nA section the artifact never had.\n"

    merged = merge(PREVIOUS, corrections)

    assert merged == PREVIOUS
    assert "A section the artifact never had." not in merged


def test_merge_preserves_section_order() -> None:
    # Corrections arriving out of order still land in the artifact's order.
    corrections = "## Gamma\n\nNew gamma.\n\n## Alpha\n\nNew alpha.\n"

    merged = merge(PREVIOUS, corrections)

    assert merged.index("New alpha.") < merged.index("Original beta body.")
    assert merged.index("Original beta body.") < merged.index("New gamma.")


def test_merge_is_idempotent_for_identical_corrections() -> None:
    # Re-supplying a section verbatim leaves the artifact byte-identical.
    alpha_section = "## Alpha\n\nOriginal alpha body.\n\n"

    assert merge(PREVIOUS, alpha_section) == PREVIOUS
    assert merge(PREVIOUS, "") == PREVIOUS


def test_merge_drops_correction_preamble_chatter() -> None:
    corrections = "Here are the corrected sections you asked for:\n\n## Beta\n\nFixed.\n"

    merged = merge(PREVIOUS, corrections)

    assert "Here are the corrected sections" not in merged
    assert "Fixed." in merged
