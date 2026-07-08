# Product Requirements Document (PRD): LLM Workspace Optimization & Interoperability Framework

## 1. Overview and Objectives
The goal of this project is to establish a standardized, highly efficient workspace architecture for utilizing Claude and custom autonomous agents. The framework will optimize token consumption, ensure appropriate model routing based on task complexity, and maintain strict context window management. It will support seamless interoperability between custom multi-loop agentic workflows (via LangChain/LangGraph) and Claude Code, specifically optimized for Ralph loop (externalized state) development patterns.

## 2. Core Requirements

### 2.1 Token Optimization & Context Management
* **Lean Root Context:** A centralized, lightweight `CLAUDE.md` will sit at the repository root. It will serve strictly as a static routing layer to maximize prompt caching, containing only critical persona definitions, behavioral guardrails, and pointers to the `.ai/` directory.
* **Referential Architecture:** Heavy documentation will not be loaded by default. `CLAUDE.md` will use explicit file paths to reference secondary documentation (e.g., `.ai/custom-instructions/api_schema.md`) only when triggered by specific task domains.

### 2.2 Model Routing & Selection
* **Phase 1: Persona-Driven Guidelines (Current):** Model routing will initially be handled via documented guidelines and dictated by specific agent personas. The user or orchestrator will manually select models based on defined complexity thresholds.
* **Phase 2: Extensible Automation:** The architecture must be designed to support a future transition to automated model selection (e.g., via a proxy or routing logic script) once the threshold logic is proven and trusted.

### 2.3 Directory Structure & State Tracking
To decouple human readability from programmatic parsing, combat context pollution, and keep the repository root clean, all agent operational data will be housed in an `.ai/` directory. State will be synchronized across two files:
* **`.ai/next-steps.md` (Human-Readable):** A live narrative ledger detailing current sprint goals, open issues, and immediate next operational steps. It provides instant context to the developer and Claude Code.
* **`.ai/state.json` (Machine-Readable):** A structured payload used by the LangChain/LangGraph agents to programmatically track variables such as `current_sprint_id`, `assigned_persona`, `status`, and active tool parameters.

### 2.4 Archival & Isolation System
* **Archival Trigger (`/archive-sprint`):** Archival is executed via a specific `/archive-sprint` skill or command. It is triggered *only* when sprint completion conditions are met. Standard state shifts like `/handoff` or `/resume` will not invoke archival.
* **Post-Archival Bootstrapping:** Upon successful execution, the system will move the current sprint data to `.ai/archive/` and automatically set up the environment for the next sprint (e.g., generating a fresh `next-steps.md` and resetting `state.json`).
* **Context Exclusion:** The `.ai/archive/` directory must be explicitly excluded from standard context-gathering tools (via `.claudesignore` and agent configuration) to prevent token bloat, while remaining accessible for manual historical queries.

### 2.5 Agent Interoperability & Tech Stack
* **Framework Integration:** The custom agent framework leverages LangChain/LangGraph, establishing a structured, stateful multi-loop architecture.
* **Seamless State Handoff:** The workspace must support a standardized protocol for pausing and resuming work to maintain a clean context window. 
* **Tool & Skill Utilization:** Native Claude skills and LangChain tools will be leveraged.
  * Example: A `/handoff` command that automatically serializes the current active context into `state.json`, summarizes the narrative into `next-steps.md`, flushes temporary memory, and preps the environment for the next persona or human-in-the-loop.
  * Example: A `/resume` command that reads the externalized state from `.ai/state.json` and `.ai/next-steps.md` to initialize a completely fresh instance. It automatically assumes the required persona and picks up the exact task where the previous model/agent left off, enabling continuous execution with zero context pollution.

### 2.6 Best Practices
* **Prompt Caching Optimization:** Root instructions remain static to leverage LLM caching mechanisms; volatile state is decoupled into separate files.
* **Security:** No hardcoded secrets in prompt files or state trackers.
* **Version Control:** Structural files will be committed via Git. Volatile state (`state.json`) and archives will be explicitly ignored to prevent noisy commits.
* **Deterministic Execution:** Agent instructions should be written to minimize hallucination and ensure predictable, repeatable actions.