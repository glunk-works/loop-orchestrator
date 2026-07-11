# loop-engine

A reusable framework for running a named, ordered sequence of decoupled AI "persona" stages against a single, explicit, versioned state object — instead of copy-pasting prompts between manual steps.

The default loop reproduces a **PM → Architecture → Agile Sprint Breakdown → Coder/IaC** pipeline: each stage reads the prior stage's output from shared `State`, calls an LLM, and writes its own output back, with a snapshot persisted to disk after every stage.

## Why

Before loop-engine, this pattern (`pm-agent-loop`) was hardcoded as a single, non-reusable CLI tightly coupled to one persona pair and one output shape. loop-engine generalizes it: personas are pluggable modules, loops are plain Python lists composing them, and every stage transition is validated, budget-checked, and written to disk as an inspectable artifact.

## Requirements

- Python >= 3.12
- [Hatch](https://hatch.pypa.io/) for environment/script management
- An Anthropic API key, stored in your OS keyring (see [Setup](#setup))
- Docker (optional) — only if you want the dev/prod containers instead of a local checkout; see [Running in a container](#running-in-a-container)

## Installation

```bash
git clone https://github.com/glunk-works/loop-engine.git
cd loop-engine
hatch run python -c "import loop_engine"  # sanity check
```

## Setup

loop-engine never accepts the API key as a CLI flag or environment variable — it is retrieved exclusively from the OS-native credential store (Windows Credential Manager / macOS Keychain / Secret Service on Linux) via [`keyring`](https://pypi.org/project/keyring/):

```bash
hatch run python -c "import keyring; keyring.set_password('loop-engine', 'anthropic_api_key', 'sk-ant-...')"
```

`src/loop_engine/tools/llm/client.py` is the only module in the codebase permitted to import `keyring` — enforced by a static test (`tests/tools/test_keyring_boundary.py`).

## Usage

### Run the default loop

```bash
hatch run loop-engine run --input path/to/requirements.md --budget 5.00
```

| Option | Description | Default |
|---|---|---|
| `--loop` | Named loop to run | `default` |
| `--input` | Path to the seed content (e.g. a requirements doc) for the initial `State` | none |
| `--budget` | Hard cap on cumulative LLM spend for the run, in USD (float) | `5.00` |
| `--resume-from` | Path to a prior `State` snapshot; resumes after the last completed stage instead of starting over | none |

Every stage's `State` snapshot is written to `state/<run_id>/<NN>_<StageName>.json` as it completes, and a terminal snapshot records how every run ended (`completed`, `failed_stage`, `budget_exceeded`, `awaiting_issue`) — the run is resumable and fully inspectable, not a black box. Exit codes: `0` completed, `2` paused on a GitHub issue, `3` budget exceeded.

### Resume an interrupted or budget-aborted run

```bash
hatch run loop-engine run --resume-from state/<run_id>/01_ArchitecturePersona.json
```

### Answer a paused run's questions (GitHub issue round-trip)

When the persona pipeline hits a question no automated layer can resolve, it files a GitHub issue (label `loop-engine/needs-human`), records the issue in the snapshot, and exits with status `awaiting_issue`. Reply on the issue with a fenced block — one `N: answer` line per question:

````markdown
```answers
1: eu-west-1
2: OIDC
```
````

then resume; the PM persona folds your answers into the spec, classifies each answer's blast radius, and the run re-enters at the right stage:

```bash
hatch run loop-engine resume --from-issue <issue number>
```

Closing the issue without an answers comment aborts the run.

### View per-stage cost/token usage

```bash
hatch run loop-engine cost-summary --run-id <run_id>
```

### Library usage

The full programmatic surface is available without the CLI:

```python
from loop_engine import DEFAULT_LOOP, LLMClient, State, run_graph_loop

initial_state = State(schema_version=3, run_id="my-run", stage_history=[], artifacts={})
llm_client = LLMClient(budget_usd=5.00)
final_state = run_graph_loop(DEFAULT_LOOP, initial_state, llm_client)
```

## Running in a container

A shared multi-stage `Dockerfile` (repo root) defines a `dev` stage (full contributor toolchain: `hatch`, `ruff`, `git`, `gh`) and a `prod` stage (minimal runtime only). Both are local-only — there's no registry publish step; build and run them yourself with plain `docker build`/`docker run`, or open the repo in VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers), which uses `.devcontainer/devcontainer.json` (targets the `dev` stage automatically).

```bash
docker build --target dev -t loop-engine:dev .
docker build --target prod -t loop-engine:prod .
```

### GPG commit signing from the host

The devcontainer bind-mounts a GPG agent socket file from the host (`${localEnv:GPG_HOST_DIR}` in `.devcontainer/devcontainer.json`) so commit-signing passphrase prompts appear in the host's own pinentry/Kleopatra, never inside the container. Set `GPG_HOST_DIR` to the directory containing your host GPG agent's socket in your host shell profile before opening/rebuilding the devcontainer; `.devcontainer/gpg-forward.sh` relays it in on every container start and no-ops with a warning if it isn't mounted.

### Credentials in a container

A bare Linux container has no OS-native keyring backend, so the prod/dev images ship a custom encrypted-file `keyring` backend (`containers/keyring_backend/cryptfile_backend.py`, wired in via `keyring`'s own backend-discovery config — not the PyPI `keyrings.cryptfile` package). `client.py`'s contract doesn't change — `keyring.get_password(...)` just resolves against whichever backend is configured. The backend reads two *file paths*, never secret values, from env vars: `LOOP_ENGINE_KEYRING_FILE` (the encrypted blob, default `/run/secrets/keyring_data.enc`) and `LOOP_ENGINE_KEYRING_PASSPHRASE_FILE` (the decryption passphrase, default `/run/secrets/keyring_passphrase`).

1. Create the encrypted keyring file once (outside the container, or inside a `dev` container shell):
   ```bash
   python -c "import keyring; keyring.set_password('loop-engine', 'anthropic_api_key', 'sk-ant-...')"
   ```
2. Run the prod image, mounting the encrypted file and its passphrase in as files — never as environment variables:
   ```bash
   docker run --rm \
     -v /path/to/keyring_data.enc:/run/secrets/keyring_data.enc:ro \
     -v /path/to/keyring_passphrase:/run/secrets/keyring_passphrase:ro \
     -v $(pwd)/state:/workspace/state \
     loop-engine:prod run --input requirements.md --budget 5.00
   ```
   The `state/` volume mount is required for `--resume-from` to work across separate `docker run` invocations — without it, each container starts with an empty `state/` directory.

#### Dev container: Infisical provisioning

The devcontainer provisions credentials from [Infisical](https://infisical.com) (project `loop-engine`, environment `dev`) instead of the manual step above, via a Universal Auth machine identity — one shared identity for the dev environment, never a per-secret static credential in the repo.

- The project itself is identified by `.infisical.json` (committed at the repo root — it holds only the project ID and default environment, never a credential; created via `infisical init`). Fill in its `workspaceId` for the real `loop-engine` project before this does anything.
- Before opening/rebuilding the devcontainer, set `INFISICAL_CLIENT_ID` and `INFISICAL_CLIENT_SECRET` in your **host** shell profile (same idea as the existing `GPG_HOST_DIR` requirement for [GPG commit signing](#gpg-commit-signing-from-the-host)) — get these from whoever administers the Infisical project; they're distributed out of band, never via Slack/email/repo.
- On every container start, `.devcontainer/infisical-start.sh` authenticates via `infisical login --method=universal-auth`, then runs `.devcontainer/seed-secrets.sh` inside `infisical run` — which injects `ANTHROPIC_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`, and `LOOP_ENGINE_KEYRING_PASSPHRASE` as env vars into that one child process only, never to disk. That script seeds the Anthropic key into the keyring backend above via the unchanged `keyring.set_password(...)` call, authenticates `gh` via `gh auth login --with-token`, and writes only the passphrase file to disk (at `/home/app/.infisical/keyring_passphrase` — the one secret that must persist, since `client.py` reads it continuously at runtime). There is no persistent Infisical daemon and no dotenv file with secret values left on disk.
- This is a dev-container-only bootstrap convenience — the prod image's credential path above (mounted `/run/secrets/...` files) is unchanged and does not depend on Infisical.

### GitHub MCP server

The devcontainer is configured (`.mcp.json`, committed at the repo root) to connect Claude Code / Cursor to GitHub's hosted remote MCP server (`https://api.githubcopilot.com/mcp`) using a bearer-token `GITHUB_PERSONAL_ACCESS_TOKEN`. GitHub's own docs list OAuth (browser login) as their top-recommended auth method for this server; this repo uses a PAT instead so the devcontainer can authenticate non-interactively and repeatably at container start with no browser involved — a deliberate tradeoff, not an oversight.

The token is sourced from Infisical the same way as the Anthropic key above: `gh auth login --with-token` seeds it into `gh`'s own credential store once per container start, and `.bashrc` derives `GITHUB_PERSONAL_ACCESS_TOKEN` fresh via `gh auth token` for any shell Claude Code/Cursor launches from — no separate copy of the token is ever written to disk. Use a fine-grained PAT scoped to just the repositories and permissions the MCP toolset needs (contents, pull requests, issues), not a broad classic PAT.

### CI/automation credential fallback

For a CI job that needs to run loop-engine for real (not just the mocked test suite) and can't practically mount a pre-encrypted keyring file, `client.py` also checks a **double-gated** env var pair before falling back to keyring:

```bash
docker run --rm \
  -e LOOP_ENGINE_ALLOW_ENV_CREDENTIAL=1 \
  -e LOOP_ENGINE_CI_API_KEY=sk-ant-... \
  loop-engine:prod run --input requirements.md --budget 5.00
```

**Both variables must be set together** — this is intentionally not a single `API_KEY`-style env var, so a leftover value in a shell can't silently bypass keyring. Use this only in CI/automation contexts; everywhere else, use the encrypted keyring file above.

## How it works

```
 human ⇄ GitHub Issue (filed by the engine; answers as ```answers comments)
              ⇅
             PM ──────────── owns project_spec; resolver of last automated resort
              ⇅
          Architect ───────── owns architecture_definition; resolves Coder questions
              ⇅
     Sprint Breakdown ─────── re-entered on "plan"-impact rework
              ⇅
            Coder ─────────── per-sprint inner loop; escalates, never guesses

 forward path per stage: persona.run() → gate → ACCEPT (snapshot, next stage)
                                              → REVISE (bounded, findings fed back)
                                              → ESCALATE (resolver ladder → issue)
```

The user engages only with the PM role; the other personas coordinate through it. Each stage's output must pass a content **gate** before the run advances. Questions a persona cannot answer escalate up a resolver ladder (Coder → Architect → PM), and whatever no automated layer resolves is filed as a GitHub issue for the human. Every resolution carries a blast-radius classification that routes rework: `task` re-runs the asking stage, `plan` re-enters Sprint Breakdown, `architecture` re-enters the Architect. Hard caps on escalations and re-plans keep every feedback edge finite — hitting a cap escalates to the human instead of looping.

- **`core/state.py`** — `State`, a Pydantic v2 model (`schema_version` 2: `run_id`, `status`, `questions`, `pending_issue`, `counters`, `stage_history`, `artifacts`) with `extra="forbid"`, so no field can silently smuggle a credential through. `RunStatus` makes termination explicit; v1 snapshots are migrated on load.
- **`core/engine.py`** — `execute_stage()`: one bounded propose → gate → accept/revise/escalate cycle, the single unit of stage progress. Gate findings feed revisions against the prior artifact — only flagged sections regenerate, merged back locally (identical findings twice stops paying and escalates); every exit path — success or any failure — persists a snapshot, so no paid work is lost to a traceback.
- **`core/graph_engine.py`** — `run_graph_loop()`: the LangGraph `StateGraph` that drives inter-stage routing (advance / re-enter by blast radius / terminate), one node per stage over the shared `execute_stage` primitive.
- **`core/gates.py`** — `ArtifactGate`: presence/JSON-shape checks, question-shaped-output detection (a model that answers with a question never advances the pipeline), and `## Open Questions` extraction.
- **`personas/base.py`** — `BasePersona`: abstract `run(state, llm_client, findings=None)`, declared `consumes`/`produces` artifact keys (pre-checked by the engine), and an overridable `resolve_questions()` hook for resolver duty. Personas receive the LLM client via injection — they cannot construct their own or touch credentials directly.
- **`personas/{pm,architecture,agile_sprint_breakdown,coder_iac}/`** — the four default personas, with batch-mode prompts (explicit assumptions + `## Open Questions`, never "ask and wait"). `PMPersona` keeps its critic revision loop with no-progress detection and folds human issue answers back into the spec; `CoderIacPersona` implements one sprint per LLM call and stops at a sprint that raises questions; on findings re-entry it re-runs only the sprint(s) whose questions were resolved, falling back to a full re-run for gate-revision findings. Sprint plans and implementation reports are written to `sprints/` as real files.
- **`loops/default/loop.py`** — `DEFAULT_LOOP`, a `Loop` of `Stage`s wiring personas, gates, the resolver ladder, and blast-radius re-entry targets. No YAML/JSON loop-definition format — loops are just Python.
- **`tools/llm/client.py`** — `LLMClient`, a thin wrapper around the Anthropic SDK. Retrieves the API key from `keyring` exactly once per instance, prices every call from a per-model rate table (`tools/llm/pricing.py`, covering input, output, and cache write/read tokens), enforces a hard per-run USD budget *before* each call (`BudgetExceededError`; the pre-flight estimate is a chars/4 heuristic, refined by the token-counting endpoint near the cap), sends each persona's stable prefix (template + consumed artifact) as cached system blocks (`cache_control: ephemeral` — cache reads bill at ~0.1x input rate), and refuses to return silently truncated output (`TruncatedResponseError` on `stop_reason == "max_tokens"`).
- **`tools/issue_io/`** — the sole GitHub caller (shells out to the already-authenticated `gh`; no token passes through the process). Files escalation issues and parses answer comments.
- **`tools/state_io/writer.py`** — the sole writer of `State` snapshots (`state/`) and produced artifacts (`docs/`, `sprints/`, `src/`). Validates `run_id`/artifact paths against path traversal before any filesystem call.
- **`tools/logging_config.py`** — structured per-stage cost logging.
- **`cli.py`** — the Typer entrypoint (`run`, `resume`, `cost-summary`). A thin wrapper; all logic lives in the library layer.

## Development

```bash
hatch run test                        # pytest
hatch run lint                        # ruff check (incl. bandit-equivalent S rules)
hatch run format                      # ruff format
hatch run audit                       # pip-audit: known-CVE scan of all pinned dependencies
hatch run sbom                        # regenerate sbom.json (CycloneDX)
```

Every sprint's changes must satisfy [`sprints/GLOBAL_DEFINITION_OF_DONE.md`](sprints/GLOBAL_DEFINITION_OF_DONE.md) — tests pass, lint/format clean, `gitleaks` finds nothing, dependencies are pinned to versions with no known critical/high CVE, and `sbom.json` is current. CI (`.github/workflows/ci.yml`) enforces all of this on every PR: `lint` → `format-check` → `test` → `secrets-scan` → `sbom`.

## Security

- The LLM API key is retrieved exclusively via `keyring` from `tools/llm/client.py` — no other module imports `keyring` (statically enforced). One documented, double-gated exception for CI/automation contexts — see [CI/automation credential fallback](#ciautomation-credential-fallback).
- `tools/state_io/` is the only module permitted to write to `state/`, `docs/`, or `sprints/`; `run_id` and artifact paths are validated against path traversal before any filesystem call.
- `core/` imports no concrete persona module, only `personas/base.py` — personas can't bypass the engine's validation/budget/persistence guarantees.
- `State.model_config = ConfigDict(extra="forbid")` — no field exists that could hold a raw credential, and a compromised/buggy persona can't smuggle one through.
- Per-run USD budget is enforced centrally — every call is priced from a per-model rate table, with the pre-flight estimate refined via the token-counting endpoint near the cap — and aborts the run *before* an over-budget call executes, not after.
- The agentic Coder executes generated tests via subprocess (`pytest`, fixed argv, no shell, hard timeout), and the Coder stage's gate re-runs them before accepting — **acceptance is evidence-based, and generated code runs with your privileges: run untrusted loops only inside the sandboxed devcontainer.** Coder tool paths are traversal- and symlink-validated; writes still go only through `tools/state_io`.

See [`docs/architecture_definition.md`](docs/architecture_definition.md) for the full architecture and threat-model writeup.

## Project layout

```
src/loop_engine/
├── core/           # State model, LangGraph engine
├── personas/       # BasePersona ABC + pm/architecture/agile_sprint_breakdown/coder_iac
├── loops/          # DEFAULT_LOOP composition
├── tools/          # llm client, state_io writer, logging config
└── cli.py          # Typer entrypoint

tests/              # mirrors src/loop_engine/ layout, plus tests/integration/
sprints/            # the sprint-by-sprint build plan and its Definition of Done
docs/               # architecture definition and project spec
Dockerfile          # multi-stage: dev (contributor toolchain) + prod (minimal runtime)
.devcontainer/      # VS Code Dev Containers config, targets the Dockerfile's dev stage
```

## License

MIT
