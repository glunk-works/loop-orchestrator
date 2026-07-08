"""`GeneratorNode` — one config-driven single-shot document persona.

Replaces the per-class boilerplate of Architecture, Sprint Breakdown, and PM.
Its only varying logic is the config-selected shared services (`services.py`):
an input-wrapper, an output-adapter, a revision-style, and an optional
`resolve_via_document` resolver. `system_blocks` are built from immutable config
+ state fields only (prompt loaded once at construction) so the cached prefix
stays byte-identical across revision attempts.

Guiding principle: *personas generate, gates accept, the graph routes.* The
node does exactly one generation (or one targeted revision) and returns; the
engine's revise loop + the stage gate provide the cycle.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from loop_engine.core.state import Question, State
from loop_engine.personas import sections
from loop_engine.personas.base import BasePersona
from loop_engine.personas.declarative import services
from loop_engine.personas.declarative.config import (
    GeneratorConfig,
    load_named_config,
    load_prompt,
)


@dataclass
class _CallContext:
    system_blocks: list[str] | None
    inline_prompt: str | None
    wrapped_inputs: list[str]


class GeneratorNode(BasePersona):
    def __init__(self, config: GeneratorConfig) -> None:
        # Validate the configured strategy names up front (fail at construction,
        # not deep inside a run).
        services.check_output_adapter(config.output_adapter)
        services.check_revision_style(config.revision_style)
        for ctx in config.input_context:
            services.get_input_wrapper(ctx.wrap)

        self.config = config
        self.consumes = tuple(config.consumes)
        self.produces = (config.produces,)
        # Loaded once, held immutably — the source of the cache-stable prefix.
        self._prompt = load_prompt(config.prompt_file)
        self._feedback_template = (
            load_prompt(config.revision_feedback_prompt_file)
            if config.revision_feedback_prompt_file
            else None
        )
        self._resolution_template = (
            load_prompt(config.resolver.prompt_file) if config.resolver else None
        )

    @property
    def _stage_name(self) -> str:
        # Matches what the engine passes to the gate (`type(persona).__name__`),
        # so open-question origin_stage lines up with the gate's matching.
        return type(self).__name__

    def _build_context(self, state: State) -> _CallContext:
        wrapped_inputs = [
            services.get_input_wrapper(ctx.wrap)(state.artifacts.get(ctx.artifact, ""), ctx.label)
            for ctx in self.config.input_context
        ]
        if self.config.prompt_style == "cached":
            # Cache-stable prefix: prompt + wrapped inputs, state-derived only.
            return _CallContext([self._prompt, *wrapped_inputs], None, wrapped_inputs)
        # inline: everything in one user prompt, no system_blocks (the classic PM
        # call shape, byte-for-byte).
        inline = self._prompt + "".join(f"\n\n{w}" for w in wrapped_inputs)
        return _CallContext(None, inline, wrapped_inputs)

    def _mergeable_prior(self, state: State):
        adapter = self.config.output_adapter
        if adapter == "json_object":
            # key_merge always has a (possibly empty) prior dict to merge into.
            return services.parse_json_object(state.artifacts.get(self.config.produces, ""))
        prior = state.artifacts.get(self.config.produces, "")
        if not prior.strip():
            return None
        if adapter == "markdown":
            # Mergeable only if the prior document has addressable sections
            # (matches classic Architecture's `sections.has_sections` guard).
            return prior if sections.has_sections(prior) else None
        # sprint_blocks: reconstruct the prior breakdown markdown from the blocks.
        try:
            blocks = json.loads(prior)
        except json.JSONDecodeError:
            return None
        if not blocks:
            return None
        return "\n\n".join(
            f"### FILEPATH: {block['path']}\n\n{block['content']}" for block in blocks
        )

    def run(self, state: State, llm_client, findings: list[str] | None = None) -> State:
        findings = findings or []
        ctx = self._build_context(state)
        prior = self._mergeable_prior(state)
        is_revision = bool(findings) and prior is not None

        if is_revision:
            raw = self._revise(llm_client, ctx, prior, findings)
        else:
            raw = self._generate(llm_client, ctx, findings)

        return self._finalize(state, raw, prior, is_revision)

    # -- generation ------------------------------------------------------- #
    def _generate(self, llm_client, ctx: _CallContext, findings: list[str]) -> str:
        if ctx.system_blocks is not None:  # cached
            prompt = self.config.initial_prompt
            if findings:
                # Findings but no mergeable prior: full regeneration with the
                # feedback inline (the classic Architecture/Sprint fallback).
                prompt += (
                    "\n\nRevision feedback on your previous attempt — address every item:\n"
                    + services.format_feedback(findings)
                )
            response = llm_client.call(
                prompt,
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system_blocks=ctx.system_blocks,
            )
        else:  # inline (PM initial extraction — findings unreachable here)
            response = llm_client.call(
                ctx.inline_prompt, model=self.config.model, max_tokens=self.config.max_tokens
            )
        return response.text

    def _revise(self, llm_client, ctx: _CallContext, prior, findings: list[str]) -> str:
        style = self.config.revision_style
        if style == "key_merge":
            return self._revise_key_merge(llm_client, ctx, findings)
        if style == "section_merge":
            return self._revise_section_merge(llm_client, ctx, prior, findings)
        # full_reextract: no prior-artifact replay, feedback inline.
        return self._generate(llm_client, ctx, findings)

    def _revise_section_merge(
        self, llm_client, ctx: _CallContext, prior, findings: list[str]
    ) -> str:
        feedback = services.format_feedback(findings)
        instruction = services.revision_instruction(self.config.output_adapter)
        response = llm_client.call_messages(
            [
                {"role": "user", "content": self.config.initial_prompt},
                {"role": "assistant", "content": prior},
                {
                    "role": "user",
                    "content": (
                        f"Revision feedback on your previous attempt — address every item:\n"
                        f"{feedback}\n\n{instruction}"
                    ),
                },
            ],
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system_blocks=ctx.system_blocks,
        )
        return response.text

    def _revise_key_merge(self, llm_client, ctx: _CallContext, findings: list[str]) -> str:
        # Dedup preserves order: the same field flagged twice must not double the
        # prompt (and identical findings twice is the engine's no-progress guard).
        deduped = list(dict.fromkeys(findings))
        wrapped_artifact = ctx.wrapped_inputs[0] if ctx.wrapped_inputs else ""
        followup = self._feedback_template.format(
            findings=services.format_feedback(deduped), artifact=wrapped_artifact
        )
        response = llm_client.call(
            followup, model=self.config.model, max_tokens=self.config.max_tokens
        )
        return response.text

    # -- finalize --------------------------------------------------------- #
    def _finalize(self, state: State, raw: str, prior, is_revision: bool) -> State:
        adapter = self.config.output_adapter
        if adapter == "markdown":
            effective = services.merge_sections(prior, raw) if is_revision else raw
            return services.finalize_markdown(
                produces=self.config.produces,
                effective_text=effective,
                raw_response=raw,
                extract_questions=self.config.extract_open_questions,
                stage_name=self._stage_name,
                state=state,
            )
        if adapter == "sprint_blocks":
            effective = services.merge_sections(prior, raw) if is_revision else raw
            return services.finalize_sprint_blocks(
                produces=self.config.produces,
                effective_text=effective,
                raw_response=raw,
                stage_name=self._stage_name,
                state=state,
            )
        # json_object
        parsed = services.parse_json_object(raw)
        return services.finalize_json_object(
            produces=self.config.produces,
            parsed=parsed,
            prior=prior if is_revision else {},
            is_revision=is_revision,
            static_fields=self.config.static_fields,
            state=state,
        )

    # -- resolver --------------------------------------------------------- #
    def resolve_questions(
        self, questions: list[Question], state: State, llm_client
    ) -> list[Question]:
        resolver = self.config.resolver
        if resolver is None:
            return questions
        return services.resolve_via_document(
            document=resolver.document,
            document_var=resolver.document_var,
            template=self._resolution_template,
            resolved_by=resolver.resolved_by,
            model=self.config.model,
            max_tokens=resolver.max_tokens,
            questions=questions,
            state=state,
            llm_client=llm_client,
        )


class ArchitectureGenerator(GeneratorNode):
    """Declarative Architecture port — distinct type name gives the stage its own
    escalation counter / question origin, exactly like the classic class."""

    def __init__(self) -> None:
        super().__init__(load_named_config("architecture"))


class SprintBreakdownGenerator(GeneratorNode):
    def __init__(self) -> None:
        super().__init__(load_named_config("sprint_breakdown"))


class PMGenerator(GeneratorNode):
    def __init__(self) -> None:
        super().__init__(load_named_config("pm"))
