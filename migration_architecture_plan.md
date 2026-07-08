# Architectural Requirements: Loop Engine AI Harness

## 1. Core Philosophy
* **Ruthless Simplicity:** The orchestrator acts as a lightweight routing hub, not a monolithic state machine.
* **Standardized Interfaces:** All tool access is delegated to Model Context Protocol (MCP) servers.
* **Deterministic Verification:** AI output is evaluated by standard compilers and test suites (exit codes), never by an LLM "Critic."
* **Multi-Repo Operations:** The engine operates as a centralized factory, deploying and maintaining code across the `glunk-works` GitHub organization.

---

## 2. Phase 1: State & Skill Externalization
* **Global Directives:** `CLAUDE.md` must be expanded to serve as the global skill and convention repository (e.g., Python formatting, OpenTofu structural rules).
* **Semantic State Persistence:** 
  * Create an `.agent/` directory to store operational context.
  * `STATE.md`: Mutable scratchpad for active task tracking and blocked items.
  * `MEMORY.md`: Append-only ledger for finalized architectural decisions and lessons learned.
* **Orchestrator State:** The LangGraph state object must be stripped of conversational/semantic history, retaining only control-flow routing variables (e.g., `active_task`, `error_count`).

---

## 3. Phase 2: Tooling Standardization (MCP)
* **Decoupling Tools:** All native Python tools (e.g., GitHub I/O, file execution) must be migrated into standalone MCP server applications.
* **Dynamic Discovery:** The engine's LLM client must dynamically discover available tools by querying the servers defined in `.mcp.json`.
* **Standardized Invocation:** Tool calls must execute over standard stdio or HTTP via the MCP client, physically separating the orchestrator from tool execution.

---

## 4. Phase 3: Execution Isolation
* **Git Worktrees:** The orchestrator must never execute agent tasks in its own working directory. Every task must be assigned a dynamically generated git worktree.
* **Sandboxed Compute:** High-risk tasks (code execution, tests) must be performed inside a disposable devcontainer/Docker container.
* **Mount Restrictions:** The execution container must only mount the specific isolated worktree for the active task.

---

## 5. Phase 4: Flattening Orchestration
* **Declarative Personas:** Persona logic (PM, Architect, Coder) must be removed from Python classes and defined in static configuration files (YAML/TOML) containing only the `system_prompt` and required `tools`.
* **Test-Driven Gates:** Python-based "Critic" logic must be deprecated. The gateway to completing a task is strictly tied to a `0` exit code from the execution MCP server (e.g., passing `pytest` or `tofu validate`).
* **Error Looping:** A non-zero exit code automatically routes the `stderr` logs back to the Coder persona for debugging until the test suite passes.

---

## 6. Phase 5: Autonomous Triggers
* **Event-Driven Invocation:** A lightweight FastAPI server must be deployed alongside the engine to listen for GitHub webhooks.
* **Trigger Conditions:** The engine initializes a workflow loop upon specific GitHub events, such as an issue being tagged with `agent-action` or a slash command in an issue comment.

---

## 7. Operational Workflows (The "Developed Thing")
* **Bootstrapping (From Scratch):**
  * The engine uses an administrative GitHub MCP tool to create a new repository within the organization.
  * It executes standardized scaffolding templates (e.g., `hatch new` for Python, boilerplate for OpenTofu) inside a fresh worktree.
  * It injects the global `CLAUDE.md` to establish ground rules.
  * It commits and pushes the baseline repository state.
* **Maintenance (Existing Repositories):**
  * The engine clones the target repository and checks out a feature branch into an isolated worktree.
  * It absorbs the target repository's local `CLAUDE.md` and `.agent/STATE.md`.
  * Upon test gate success, the GitHub MCP server pushes the branch and opens a Pull Request against `develop` (or a designated integration branch).
  * Auto-merging is strictly prohibited; human review or remote CI/CD pipeline validation is required.