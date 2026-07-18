import textwrap

import pytest
import yaml

from loop_orchestrator.personas.declarative import config as config_module
from loop_orchestrator.personas.declarative.config import (
    GeneratorConfig,
    load_generator_config,
    load_prompt,
    repo_root,
)

# An existing prompt file so the exists-validator passes on the happy path.
_REAL_PROMPT = "prompts/02_architecture_definition_prompt.md"

_VALID = textwrap.dedent(
    f"""
    name: sample
    prompt_file: {_REAL_PROMPT}
    model: claude-sonnet-5
    max_tokens: 64000
    consumes: [project_spec]
    produces: architecture_definition
    initial_prompt: "Begin now."
    input_context:
      - artifact: project_spec
        label: "Project Specification Document"
        wrap: none
    output_adapter: markdown
    revision_style: section_merge
    extract_open_questions: true
    """
)


def _write(tmp_path, text: str):
    path = tmp_path / "cfg.yaml"
    path.write_text(text)
    return path


def test_valid_config_loads(tmp_path) -> None:
    cfg = load_generator_config(_write(tmp_path, _VALID))
    assert isinstance(cfg, GeneratorConfig)
    assert cfg.name == "sample"
    assert cfg.output_adapter == "markdown"
    assert cfg.input_context[0].label == "Project Specification Document"
    assert cfg.prompt_style == "cached"  # default


def test_unknown_top_level_key_rejected(tmp_path) -> None:
    with pytest.raises(Exception, match="extra_forbidden|Extra inputs"):
        load_generator_config(_write(tmp_path, _VALID + "\nmystery_key: 1\n"))


def test_bad_output_adapter_enum_rejected(tmp_path) -> None:
    bad = _VALID.replace("output_adapter: markdown", "output_adapter: xml_blob")
    with pytest.raises(Exception, match="output_adapter"):
        load_generator_config(_write(tmp_path, bad))


def test_bad_revision_style_enum_rejected(tmp_path) -> None:
    bad = _VALID.replace("revision_style: section_merge", "revision_style: rewrite_all")
    with pytest.raises(Exception, match="revision_style"):
        load_generator_config(_write(tmp_path, bad))


def test_bad_wrap_enum_rejected(tmp_path) -> None:
    bad = _VALID.replace("wrap: none", "wrap: encrypt")
    with pytest.raises(Exception, match="wrap"):
        load_generator_config(_write(tmp_path, bad))


def test_missing_required_field_rejected(tmp_path) -> None:
    bad = _VALID.replace("produces: architecture_definition\n", "")
    with pytest.raises(Exception, match="produces"):
        load_generator_config(_write(tmp_path, bad))


def test_nonexistent_prompt_file_rejected(tmp_path) -> None:
    bad = _VALID.replace(_REAL_PROMPT, "prompts/does_not_exist.md")
    with pytest.raises(Exception, match="prompt file"):
        load_generator_config(_write(tmp_path, bad))


def test_python_object_tag_does_not_instantiate(tmp_path) -> None:
    # yaml.safe_load must refuse the !!python/object tag rather than construct
    # anything — the prompt-injection / RCE guard on the config format.
    hostile = _VALID + "\nstatic_fields: !!python/object/apply:os.system ['echo pwned']\n"
    with pytest.raises(yaml.YAMLError):
        load_generator_config(_write(tmp_path, hostile))


def test_loader_uses_safe_load(monkeypatch, tmp_path) -> None:
    # Guard: the loader must go through yaml.safe_load (never the unsafe
    # yaml.load with a full constructor). Spy that safe_load is the entrypoint.
    calls: list[str] = []
    real_safe_load = config_module.yaml.safe_load

    def _spy(stream):
        calls.append("safe_load")
        return real_safe_load(stream)

    monkeypatch.setattr(config_module.yaml, "safe_load", _spy)
    cfg = load_generator_config(_write(tmp_path, _VALID))
    assert cfg.name == "sample"
    assert calls == ["safe_load"]


def test_loader_source_never_calls_unsafe_yaml_load() -> None:
    source = (repo_root() / "src/loop_orchestrator/personas/declarative/config.py").read_text()
    assert "yaml.safe_load" in source
    assert "yaml.load(" not in source


def test_repo_root_contains_pyproject() -> None:
    assert (repo_root() / "pyproject.toml").is_file()
    assert (repo_root() / _REAL_PROMPT).is_file()


def test_load_prompt_decodes_non_ascii_as_utf8(monkeypatch, tmp_path) -> None:
    # Review finding #5: with no explicit encoding, read_text() decodes with
    # the platform-default codec, which raises UnicodeDecodeError under a
    # C/POSIX locale on a file containing an em-dash (U+2014).
    monkeypatch.setattr(config_module, "repo_root", lambda: tmp_path)
    (tmp_path / "prompt.md").write_bytes("Some text — with an em-dash.".encode())
    assert load_prompt("prompt.md") == "Some text — with an em-dash."


def test_load_generator_config_decodes_non_ascii_as_utf8(tmp_path) -> None:
    non_ascii = _VALID.replace(
        'label: "Project Specification Document"',
        'label: "Project Specification — Document"',
    )
    cfg = load_generator_config(_write(tmp_path, non_ascii))
    assert cfg.input_context[0].label == "Project Specification — Document"


def test_bundled_prompt_files_contain_em_dash_and_decode_cleanly() -> None:
    # The referenced prompt files (00_pm_*, 02_*, 03_*) contain U+2014 for
    # real — this is a regression test against the actual shipped assets, not
    # just synthetic ones.
    assert "—" in load_prompt("prompts/00_pm_extraction_prompt.md")
    assert "—" in load_prompt("prompts/02_architecture_definition_prompt.md")
