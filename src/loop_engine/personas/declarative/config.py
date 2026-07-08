"""Declarative `GeneratorNode` config — a Pydantic-validated boundary.

A per-persona YAML file (loaded with `yaml.safe_load` only) describes a
single-shot document persona: which prompt file to load, model/token budget,
consumed/produced artifacts, how the input is wrapped, which output-adapter and
revision-style services to dispatch to, and an optional resolver. The config is
a trusted in-repo asset, but the loader still refuses `yaml.load` so a malformed
or hostile file can never instantiate code.

Prompt files are referenced repo-root-relative (e.g. `prompts/02_...md`), the
same convention `tests/personas/test_prompt_parity.py` uses; the model loads and
pins them at construction so cached `system_blocks` stay byte-stable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

OutputAdapter = Literal["markdown", "sprint_blocks", "json_object"]
RevisionStyle = Literal["section_merge", "key_merge", "full_reextract"]
PromptStyle = Literal["cached", "inline"]
WrapStyle = Literal["none", "untrusted"]


def repo_root() -> Path:
    """Repo root, found by walking up to the `pyproject.toml` marker.

    Prompt files live at `<root>/prompts/`; config files ship inside the
    package. Anchoring on the marker (not `Path.cwd()`) keeps prompt resolution
    correct under worktree isolation, which `chdir`s the run elsewhere.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    # Fallback: src/loop_engine/personas/declarative/config.py → repo root.
    return here.parents[4]


def resolve_prompt_path(prompt_file: str) -> Path:
    return repo_root() / prompt_file


def load_prompt(prompt_file: str) -> str:
    return resolve_prompt_path(prompt_file).read_text()


class InputContext(BaseModel):
    """One consumed artifact rendered into the prompt, optionally wrapped."""

    model_config = ConfigDict(extra="forbid")

    artifact: str = Field(min_length=1)
    label: str = ""
    wrap: WrapStyle = "none"


class ResolverConfig(BaseModel):
    """`resolve_via_document`: answer escalated questions from an owned document.

    Reproduces `Architecture.resolve_questions` / `PM.resolve_questions` — the
    resolution prompt (with `{questions}` + a document placeholder) is loaded
    from `prompt_file`, the owned `document` artifact fills `document_var`, and
    `apply_resolution_response` stamps `resolved_by`.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["resolve_via_document"] = "resolve_via_document"
    document: str = Field(min_length=1)
    document_var: str = Field(min_length=1)
    prompt_file: str = Field(min_length=1)
    resolved_by: str = Field(min_length=1)
    max_tokens: int = Field(gt=0)


class GeneratorConfig(BaseModel):
    """Declarative description of one single-shot document persona."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    prompt_file: str = Field(min_length=1)
    model: str = Field(min_length=1)
    max_tokens: int = Field(gt=0)
    consumes: list[str] = Field(default_factory=list)
    produces: str = Field(min_length=1)
    initial_prompt: str = ""
    input_context: list[InputContext] = Field(default_factory=list)
    output_adapter: OutputAdapter
    revision_style: RevisionStyle
    extract_open_questions: bool = False
    # `cached` (Architecture/Sprint): prompt + inputs in cached system_blocks,
    # `initial_prompt` in the user turn. `inline` (PM): everything in one user
    # prompt, no system_blocks — matching the classic PM call byte-for-byte.
    prompt_style: PromptStyle = "cached"
    # Baseline keys merged into a `json_object` output (e.g. PM's
    # `revision_history: []`) so the produced JSON is byte-identical to the
    # classic persona's on the clean path. Not an accumulator — a static prefix.
    static_fields: dict[str, object] = Field(default_factory=dict)
    # PM's `key_merge` followup wording differs from the generic section-merge
    # feedback; when set, this file is the followup prompt template.
    revision_feedback_prompt_file: str | None = None
    resolver: ResolverConfig | None = None

    @model_validator(mode="after")
    def _prompt_files_exist(self) -> GeneratorConfig:
        missing: list[str] = []
        for candidate in (
            self.prompt_file,
            self.revision_feedback_prompt_file,
            self.resolver.prompt_file if self.resolver else None,
        ):
            if candidate is not None and not resolve_prompt_path(candidate).is_file():
                missing.append(candidate)
        if missing:
            raise ValueError(f"prompt file(s) not found: {missing}")
        return self


def load_generator_config(path: str | Path) -> GeneratorConfig:
    """Load a `GeneratorConfig` from a YAML file (`yaml.safe_load` only)."""
    raw = Path(path).read_text()
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(
            f"generator config {path} must be a YAML mapping, got {type(data).__name__}"
        )
    return GeneratorConfig.model_validate(data)


_CONFIG_DIR = Path(__file__).resolve().parent / "configs"


def load_named_config(name: str) -> GeneratorConfig:
    """Load a bundled config by base name (`architecture`/`sprint_breakdown`/`pm`)."""
    return load_generator_config(_CONFIG_DIR / f"{name}.yaml")
