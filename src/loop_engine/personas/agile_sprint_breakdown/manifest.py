"""Structured task manifest derived from the Sprint Breakdown output.

The Agile sprint files decompose work into sprints → tasks → acceptance
criteria — exactly the discrete, dependency-ordered, independently-verifiable
checklist a Ralph-loop Coder needs to terminate. This module derives a
machine-readable `task_manifest` from the same markdown the Sprint Breakdown
persona already produces — **deterministically, with no extra LLM call** — so
the executor never re-parses prose per iteration.

`sprint_plans` is unchanged; the manifest is an additive view over it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from loop_engine.core.gates import ArtifactGate, GateDecision, GateResult
from loop_engine.core.state import State

# The Sprint Breakdown prompt rigidly mandates this structure (see
# prompts/03_agile_sprint_breakdown_prompt.md), the same rigidity
# `_parse_sprint_blocks` already relies on for `### FILEPATH:` headers.
_TASK_HEADER_RE = re.compile(r"^\s*[-*]\s*\*\*Task\s+(\d+)\s*:\s*(.+?)\*\*\s*$", re.MULTILINE)
_DEPENDENCIES_RE = re.compile(
    r"\*\*Dependencies:\*\*\s*(.*?)(?=\n\s*[-*]?\s*\*\*[A-Z]|\Z)", re.DOTALL
)
_LEADING_NUMBER_RE = re.compile(r"^(\d+)")
# A number counts as a sprint reference only when sprint-qualified (`Sprint 3`,
# `Sprint #3`, `#3`) — never a bare digit, which would forge a dependency from
# an incidental number in the prose (`OAuth2`, `RFC 6749`).
_SPRINT_NUMBER_REF_RE = re.compile(r"(?:sprint\s*#?\s*|#)0*(\d+)", re.IGNORECASE)


class TaskEntry(BaseModel):
    """One atomic, independently-verifiable unit of work from a sprint file."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    sprint_path: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    acceptance_criteria: str = ""
    target_files: list[str] = Field(default_factory=list)
    # Task ids that must be done before this one: prior tasks in the same
    # sprint (implicit sequential) plus every task of any sprint this sprint's
    # `Dependencies:` field names.
    deps: list[str] = Field(default_factory=list)


def _sprint_dir(sprint_path: str) -> str:
    """`/sprints/NN_name/sprint_plan.md` → `NN_name` (the stable id prefix)."""
    parts = sprint_path.lstrip("/").split("/")
    if len(parts) >= 2 and parts[0] == "sprints":
        return parts[1]
    return parts[0] if parts else sprint_path


def _leading_number(text: str) -> str | None:
    match = _LEADING_NUMBER_RE.match(text)
    return str(int(match.group(1))) if match else None


def _extract_field(block: str, label: str) -> str:
    """The value of a `**Label:**` sub-bullet up to the next labelled bullet."""
    pattern = re.compile(
        rf"\*\*{re.escape(label)}:\*\*\s*(.*?)(?=(?:\n\s*[-*]\s*\*\*[A-Z])|\Z)", re.DOTALL
    )
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def _parse_target_files(raw: str) -> list[str]:
    if not raw:
        return []
    files: list[str] = []
    for part in re.split(r"[,\n]", raw):
        cleaned = re.sub(r"^[-*]\s*", "", part.strip()).strip("`[] ").strip()
        if cleaned and cleaned.upper() not in ("NONE", "N/A"):
            files.append(cleaned)
    return files


def _tasks_for_block(sprint_path: str, content: str) -> list[TaskEntry]:
    sprint_dir = _sprint_dir(sprint_path)
    headers = list(_TASK_HEADER_RE.finditer(content))
    tasks: list[TaskEntry] = []
    for index, header in enumerate(headers):
        number = int(header.group(1))
        title = header.group(2).strip()
        start = header.end()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(content)
        block = content[start:end]
        tasks.append(
            TaskEntry(
                id=f"{sprint_dir}::t{number:02d}",
                sprint_path=sprint_path,
                title=title,
                description=_extract_field(block, "Description"),
                acceptance_criteria=_extract_field(block, "Acceptance Criteria"),
                target_files=_parse_target_files(_extract_field(block, "Target Files")),
                deps=[task.id for task in tasks],  # prior tasks in this sprint
            )
        )
    return tasks


def _dependency_sprint_paths(
    content: str,
    earlier_paths: list[str],
    sprint_numbers: dict[str, str | None],
    sprint_dirs: dict[str, str],
) -> list[str]:
    """Which earlier sprint paths this sprint's `Dependencies:` field names.

    Matched by sprint-qualified number tokens (`Sprint 3`, `#3`) or by a sprint
    directory/name token (`01_ci_cd_foundation` / `ci_cd_foundation`) appearing
    whole in the field. Bare digits are ignored so an incidental number never
    forges a dependency. If the field is non-empty and not "None" but nothing
    matches, conservatively depend on the immediately preceding sprint so plan
    order is never violated.
    """
    match = _DEPENDENCIES_RE.search(content)
    if not match or not earlier_paths:
        return []
    text = match.group(1).strip()
    if not text or text.upper().startswith("NONE"):
        return []
    lowered = text.lower()
    wanted_numbers = {str(int(tok)) for tok in _SPRINT_NUMBER_REF_RE.findall(text)}
    matched: list[str] = []
    for path in earlier_paths:
        if sprint_numbers.get(path) in wanted_numbers:
            matched.append(path)
            continue
        dir_name = sprint_dirs.get(path, "").lower()
        name_only = re.sub(r"^\d+_", "", dir_name)
        tokens = [tok for tok in (dir_name, name_only) if tok]
        if any(re.search(rf"\b{re.escape(tok)}\b", lowered) for tok in tokens):
            matched.append(path)
    if matched:
        return matched
    return earlier_paths[-1:]


def build_task_manifest(sprint_blocks: list[dict]) -> list[TaskEntry]:
    """Derive the ordered task manifest from parsed sprint blocks.

    Deterministic: parses each block's `**Task N:**` structure and wires deps
    (intra-sprint sequential + cross-sprint from `Dependencies:`). A sprint whose
    tasks do not parse contributes zero tasks — the manifest gate turns that into
    a REVISE rather than silently under-scoping the run.
    """
    per_sprint: list[tuple[str, list[TaskEntry]]] = []
    sprint_numbers: dict[str, str | None] = {}
    sprint_dirs: dict[str, str] = {}
    for block in sprint_blocks:
        path = block.get("path", "")
        content = block.get("content", "")
        per_sprint.append((path, _tasks_for_block(path, content)))
        sprint_dirs[path] = _sprint_dir(path)
        sprint_numbers[path] = _leading_number(sprint_dirs[path])

    tasks_by_path = {path: tasks for path, tasks in per_sprint}
    for index, (_path, tasks) in enumerate(per_sprint):
        content = sprint_blocks[index].get("content", "")
        earlier_paths = [p for p, _ in per_sprint[:index]]
        dep_paths = _dependency_sprint_paths(content, earlier_paths, sprint_numbers, sprint_dirs)
        cross_ids = [task.id for dep in dep_paths for task in tasks_by_path[dep]]
        for task in tasks:
            task.deps = list(dict.fromkeys([*task.deps, *cross_ids]))

    return [task for _, tasks in per_sprint for task in tasks]


def _find_cycle(tasks: list[TaskEntry]) -> list[str] | None:
    graph = {task.id: list(task.deps) for task in tasks}
    color: dict[str, int] = {}  # 1 = on the current path, 2 = fully explored
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = 1
        path.append(node)
        for nxt in graph.get(node, []):
            if nxt not in graph:  # dangling dep — reported separately
                continue
            if color.get(nxt) == 1:
                return path[path.index(nxt) :] + [nxt]
            if color.get(nxt) is None:
                found = visit(nxt)
                if found:
                    return found
        path.pop()
        color[node] = 2
        return None

    for task_id in graph:
        if color.get(task_id) is None:
            found = visit(task_id)
            if found:
                return found
    return None


def validate_manifest(manifest_raw: str, sprint_plans_raw: str) -> list[str]:
    """Structural checks on the `task_manifest` artifact. Empty list ⇒ valid."""
    try:
        data = json.loads(manifest_raw) if manifest_raw.strip() else None
    except json.JSONDecodeError as exc:
        return [f"task_manifest is not valid JSON: {exc}"]
    if not isinstance(data, list) or not data:
        return ["task_manifest is missing or empty; the sprint breakdown produced no tasks"]
    try:
        tasks = [TaskEntry.model_validate(item) for item in data]
    except ValidationError as exc:
        return [f"task_manifest contains an invalid task entry: {exc}"]

    findings: list[str] = []
    ids = {task.id for task in tasks}

    covered = {task.sprint_path for task in tasks}
    try:
        blocks = json.loads(sprint_plans_raw)
    except json.JSONDecodeError:
        blocks = []
    for block in blocks if isinstance(blocks, list) else []:
        path = block.get("path") if isinstance(block, dict) else None
        if path and path not in covered:
            findings.append(
                f"sprint {path!r} produced no parseable tasks; every sprint must "
                "yield at least one task with the standard `**Task N:**` structure"
            )

    for task in tasks:
        for dep in task.deps:
            if dep not in ids:
                findings.append(f"task {task.id!r} depends on unknown task {dep!r}")

    cycle = _find_cycle(tasks)
    if cycle:
        findings.append(f"task dependency cycle detected: {' -> '.join(cycle)}")

    return findings


@dataclass(frozen=True)
class ManifestArtifactGate:
    """Sprint-Breakdown gate that also validates the `task_manifest` artifact.

    Composes the classic `sprint_plans` content gate (preserving its Open
    Questions escalation), then applies `validate_manifest`. Wired into the
    Sprint-Breakdown stage only under `LOOP_ENGINE_CODER=ralph`; the classic
    path keeps the plain `ArtifactGate`.
    """

    sprint_plans_key: str = "sprint_plans"
    manifest_key: str = "task_manifest"

    def __call__(self, state: State, stage_name: str) -> GateResult:
        base = ArtifactGate(self.sprint_plans_key, parse_json="list", require_nonempty_parse=True)
        base_result = base(state, stage_name)
        if base_result.decision is not GateDecision.ACCEPT:
            return base_result

        findings = validate_manifest(
            state.artifacts.get(self.manifest_key, ""),
            state.artifacts.get(self.sprint_plans_key, ""),
        )
        if findings:
            return GateResult(GateDecision.REVISE, findings=findings)
        return GateResult(GateDecision.ACCEPT)
