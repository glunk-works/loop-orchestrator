import textwrap

import pytest
import yaml

from loop_engine.personas.declarative import config as config_module
from loop_engine.personas.declarative.config import (
    GeneratorConfig,
    load_generator_config,
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
    source = (repo_root() / "src/loop_engine/personas/declarative/config.py").read_text()
    assert "yaml.safe_load" in source
    assert "yaml.load(" not in source


def test_repo_root_contains_pyproject() -> None:
    assert (repo_root() / "pyproject.toml").is_file()
    assert (repo_root() / _REAL_PROMPT).is_file()
