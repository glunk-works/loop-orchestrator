# loop-engine — Requirements Artifact (draft input for PM persona)

> **Purpose of this file:** this is an *existing artifact*, not a finished
> spec. Feed it to the PM persona as-is
> (`pm-agent-loop run --artifact-path ./requirements.md --output ./docs/project_spec.json`)
> so the interview starts from targeted gap-filling instead of a blank
> "raw idea" interview. Every field below is either a firm answer the human
> already gave, or is explicitly marked `OPEN` where the PM should ask
> rather than assume. Fields marked `DRAFT — needs confirmation` are an
> inferred best guess the PM should present back for explicit sign-off,
> per this project's own `interview_behavior.priority_and_estimates` rule.

## problem_statement

`pm-agent-loop` proved out a working pattern — PM interview → Critic
review → Architecture definition → Agile sprint breakdown → Coder/IaC
implementation — but that pattern is hardcoded as a single, non-reusable
CLI (`src/pm_agent_loop/`) tightly coupled to one persona pair (PM +
Critic) and one output shape (`ProjectSpec`). The four downstream stages
(architecture, sprint breakdown, coder/IaC) exist today only as loose
prompt files (`prompts/01`–`04`) that a human copy-pastes between
manually — there is no engine that runs a defined sequence of persona
stages against shared, explicit state, and no way to add a new persona or
recompose the stage order without editing the core package.

## purpose_and_goals

Build **loop-engine**: a reusable framework that executes a named,
ordered sequence of decoupled persona modules — by default **PM →
Architecture → Agile Sprint Breakdown → Coder/IaC** — against a single,
explicit, versioned state object, automatically carrying each stage's
output into the next stage's input. Personas must be pluggable modules,
not logic baked into the core engine, so new personas or alternate loop
orderings can be added without modifying `core/`.

## target_users

Primary: the repo owner (Jared), for personal/side projects — same
target-user framing as `pm-agent-loop`. Design intent: generic/reusable
enough that other loop compositions or personas could be plugged in
later, and that `pm-agent-loop`'s own PM/Critic logic could eventually be
re-expressed as loop-engine persona modules (not committed to for v1 —
see `open_questions_for_architect`).

## in_scope

- A core execution engine (`src/loop_engine/core/`) that drives a
  sequence of persona stages against shared state — a state machine, not
  a hardcoded call chain.
- An explicit, versioned **State** definition (`src/loop_engine/core/` or
  a dedicated state module) that every persona reads from and writes to.
  State must be a first-class, inspectable artifact at every stage
  boundary — not an implicit hand-off of raw prompt output between
  manual steps, which is today's `pm-agent-loop` limitation.
- A **persona** plugin interface (`src/loop_engine/personas/`) with four
  default modules generalizing the four existing prompt files:
  `pm/`, `architecture/`, `agile_sprint_breakdown/`, `coder_iac/`. Each
  persona is an independently testable module conforming to a common
  contract (exact shape left to the architect).
- A **loops** package (`src/loop_engine/loops/`) that composes personas
  into a named, ordered sequence over shared state. The default loop is
  `pm -> architecture -> agile_sprint_breakdown -> coder_iac`. Loop
  definitions must be addable without modifying persona internals.
- A **tools** package (`src/loop_engine/tools/`) holding capabilities
  shared across personas — LLM client abstraction, state persistence/IO,
  logging — generalizing `pm-agent-loop`'s `llm/`, `spec_io.py`, and
  `logging_config.py` into reusable, persona-agnostic modules.
- A top-level `tests/` suite mirroring the `src/loop_engine/` layout.
- Repository scaffold at `glunk-works/loop-engine` (new repo, does not
  yet exist).

## out_of_scope / non_goals

- OPEN — the human has not stated non-goals yet. Candidates to confirm
  with the human: non-linear/branching loops, parallel persona
  execution, a GUI/web front end, automatic invocation of one loop from
  another. Do not assume any of these are excluded without asking.

## functional_requirements

- Directory layout (human-specified, firm):
  `src/loop_engine/core/`, `src/loop_engine/tools/`,
  `src/loop_engine/personas/`, `src/loop_engine/loops/`, `tests/` at
  repo root (or something close to this shape — minor deviations are the
  architect's call, the four-package split under `core/tools/personas/loops`
  is not).
- State must be explicitly defined and versioned — not inferred from
  whatever a persona happened to output last.
- Personas must be decoupled modules: `core/` must not import
  persona-specific logic, and adding a persona must not require editing
  `core/`.
- The default reference loop must reproduce, end-to-end, the same four
  stages `pm-agent-loop` currently runs by hand via `prompts/01`–`04`.
- OPEN — human to confirm: does loop-engine need a CLI entrypoint (like
  `pm-agent-loop`'s Typer CLI) for v1, or is a library-only interface
  sufficient initially?

## integration_context

Bootstrapping constraint (explicitly named by the human): loop-engine
cannot build itself, because it doesn't exist yet — "standing in the
bucket I'm trying to lift." The intended bootstrap path is to run
loop-engine's own spec/architecture/sprint-breakdown through
`pm-agent-loop`'s **already-implemented, tested** PM → Critic →
Architecture → Sprint-Breakdown pipeline (treating `pm-agent-loop` as an
external tool operating on this requirements file), and only then
implement `glunk-works/loop-engine` itself sprint-by-sprint via the
Coder/IaC stage. loop-engine's relationship to `pm-agent-loop` long-term
(does `pm-agent-loop` later migrate onto loop-engine, or do they stay
independent?) is OPEN — see `open_questions_for_architect`.

Repository: new repo, `glunk-works/loop-engine` (org confirmed to exist
and be accessible; repo itself not yet created).

## acceptance_criteria

OPEN — draft candidates for the PM to confirm with the human rather than
assume final:
- A named loop can be run end-to-end and produces state that validates
  against the defined State schema at every stage transition.
- A new persona can be added under `personas/` and wired into a loop
  definition under `loops/` without modifying any file in `core/`.
- The default loop, run against a sample input, produces the same four
  artifact types (spec, architecture doc, sprint plans, implementation)
  that `pm-agent-loop`'s manual process produces today.

## priority_ranking

DRAFT — needs confirmation. Inferred from the conversation:
- **must_have_v1:** explicit State definition/schema; core engine
  (state machine driving stage transitions); the four default personas
  as decoupled modules; the default 4-stage loop definition; shared
  tools package (LLM client + state IO); repo scaffold matching the
  requested directory layout.
- **later/nice-to-have:** additional loop types beyond the default
  sequence; automatic loop-to-loop chaining; non-linear/parallel
  execution; resumable sessions persisted across process restarts
  (note: `pm-agent-loop` explicitly deferred resumability to "later" —
  confirm whether loop-engine's "state must be defined" requirement
  implies resumability is now in scope, or just in-process state
  visibility).

## timeline_and_cost_estimates

OPEN — ask human.

## risks_and_assumptions

- **Bootstrapping risk (named by the human):** building the framework
  that is supposed to run the PM→Architecture→Sprint→Coder pipeline by
  using that exact pipeline, manually, before the framework exists.
  Mitigation direction: treat `pm-agent-loop` as a throwaway/external
  bootstrap tool for this one task rather than trying to stand up
  loop-engine's own orchestrator first.
- **Prompt-drift risk:** the four persona behaviors currently live as
  loose prompt files in `pm-agent-loop/prompts/01`–`04`. Porting them
  into loop-engine persona modules risks silent behavioral drift from
  the originals if not done deliberately (e.g. diffed/reviewed against
  the source prompts during the coder/IaC stage).
- **Premature-generalization risk:** generalizing a 1-loop, 2-persona
  system into an N-loop, N-persona framework before a second concrete
  loop exists to validate the abstraction. Assumption to confirm with
  human: is the default 4-stage loop the *only* loop needed for v1, or
  is a second loop type planned soon enough to justify the abstraction
  now?

## security_and_risk_considerations

OPEN — ask human. Likely candidates by precedent from `pm-agent-loop`
(LLM API key handling via OS keyring, no secrets logged/committed,
distinct access levels if any) should not be assumed identical without
asking — loop-engine's shape (framework vs. single CLI) may change the
answer.

## regulatory_and_compliance_constraints

OPEN — ask human.

## supply_chain_security_expectations

OPEN — ask human. Reference point only, not an assumed answer:
`pm-agent-loop` uses ruff+bandit, Dependabot, gitleaks, and CycloneDX
SBOM generation.

## cost_sensitivity

OPEN — ask human.

## open_questions_for_architect

- Execution/consumption model: standalone Python library/CLI, a Claude
  Code skill/subagent, or both — same open question `pm-agent-loop`
  itself had unresolved at its own architecture stage.
- Exact persona plugin contract: abstract base class, protocol,
  entry-point/registry-based discovery, or config-driven — "decoupled
  module" is a requirement, not yet a mechanism.
- Exact State schema/versioning/persistence mechanism (Pydantic models
  per `pm-agent-loop` precedent is a hint from existing repo
  conventions, not a confirmed decision).
- Exact `loops/` definition format: pure Python (ordered list of
  persona classes) vs. a declarative config file (YAML/JSON) that's
  engine-agnostic.
- Long-term relationship between `loop-engine` and `pm-agent-loop`: does
  `pm-agent-loop` migrate to depend on loop-engine once it exists, do
  the two stay fully independent, or does loop-engine vendor/replace
  `pm-agent-loop`'s CLI entirely?
- Quality gates / Definition of Done are derived downstream by the
  sprint-breakdown stage from the Architecture Definition Document, per
  `pm-agent-loop` precedent — not gathered here.
