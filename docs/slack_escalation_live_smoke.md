# Slack escalation round-trip — live smoke runbook

**Purpose.** One live, end-to-end verification of the Slack **escalation round-trip** (BL-2 pass 3),
which incidentally also exercises pass 2's inbound command path. This is the check the hermetic test
suite **structurally cannot** make: the suite runs entirely against a fake `WebClient`/listener with
hand-built envelopes, so it can prove the *logic* but never that a **real** Socket Mode delivery
matches the daemon's payload-shape assumptions or that the Slack app is configured correctly.

Tracked as **BL-37**. This is an **operator-run manual smoke**, not a `live-verify` V-run — it needs a
configured Slack app, a long-lived daemon, a run engineered to pause on an escalation, a **human in the
loop** to post the thread reply, and **real Anthropic spend**. Authorize it deliberately.

> **Cost + side effects.** A short run plus one resume, hard-capped by `--budget` (≈ a couple dollars at
> most). Real messages are posted to a real Slack channel. No GitHub repos are created (unlike factory
> V-runs), so there is no repo teardown — only the daemon and a local `state/<run_id>` dir to clean up.

---

## 1. Prerequisites

**Credentials + keyring**
- Real Anthropic key in the OS keyring (the run spends money; the key is keyring-only, never a flag/env var).
- Slack **bot token** + **app-level token** + **channel** already working from pass 1/2:
  `LOOP_ORCHESTRATOR_SLACK_BOT_TOKEN`, `LOOP_ORCHESTRATOR_SLACK_APP_TOKEN` (`xapp-…`, `connections:write`),
  `LOOP_ORCHESTRATOR_SLACK_CHANNEL` (prefer the channel **ID**).

**New pass-3 Slack app config (the most likely point of failure — do this first, verify it exists)**
1. **Event Subscriptions → Subscribe to bot events → add `message.channels`.** (Delivered over the same
   Socket Mode connection; no Request URL needed.)
2. **OAuth & Permissions → Bot Token Scopes → add `channels:history`.**
3. **Reinstall the app** to the workspace (adding a scope requires reinstall) and confirm the bot is a
   member of `LOOP_ORCHESTRATOR_SLACK_CHANNEL`.

**Transport selection**
- `LOOP_ORCHESTRATOR_ESCALATION_TRANSPORT=slack` in the daemon's *and* the run's environment. (Default is
  `issue`; only `slack` routes escalations to Slack. `build_escalation_filer_from_env()` fails closed if
  `=slack` but the Slack vars are missing — a good pre-flight: a misconfigured run refuses to start.)

---

## 2. Force an escalation (the tricky part)

The round-trip only fires if a run actually **pauses `AWAITING_SLACK`** — i.e. a stage raises an
`## Open Questions` block that no resolver in the ladder (Coder → Architect → PM → human) can answer, so
it reaches the human. Two things to know:

- The **PM stage cannot escalate semantic problems today** (BL-7) — its gate is structural. Escalations
  that reach a human come from the **Architect** or **Sprint Breakdown** stages raising open questions.
- So craft a requirements doc with a **genuine product ambiguity only a human can decide** — something
  the Architect must ask about rather than assume. Keep the rest tiny so the run reaches that stage
  cheaply.

Example `forced_escalation.md`:

```markdown
# Requirements: session token store

Build a service that stores user session tokens.

Hard constraints (both stated, deliberately in tension — do not resolve on your own):
- Tokens MUST be durable across a full hardware failure (survive a node loss with zero token loss).
- Tokens MUST NOT be written to any persistent storage, ever (memory-only, nothing on disk).

Decide nothing about this contradiction yourself — it is a product decision.
```

That contradiction (durable-across-hardware-failure vs. never-persisted) is unresolvable without a human
product call, which is exactly what should escalate. If a given model run resolves or ACCEPTs it anyway,
sharpen the doc (add a second explicit "escalate, do not assume" instruction, or a second contradiction)
and retry — see BL-7 for why the PM stage in particular won't raise it.

---

## 3. Run the smoke

All commands run **from the main checkout** (the correlation scan is CWD-relative — a daemon started
elsewhere sees no snapshots). Use `infisical run` so the three `LOOP_ORCHESTRATOR_SLACK_*` vars + the
transport selector are inherited.

**Terminal A — the daemon:**
```bash
LOOP_ORCHESTRATOR_ESCALATION_TRANSPORT=slack infisical run -- hatch run loop-orchestrator slack-listen
```
Confirm it opens the socket and blocks (fails closed with a clear message if any var is missing).

**Terminal B — a run that will pause (same checkout):**
```bash
LOOP_ORCHESTRATOR_ESCALATION_TRANSPORT=slack infisical run -- \
  hatch run loop-orchestrator run --input forced_escalation.md --budget 2.00
```
Expected: the run pauses and **exits code 5** (`AWAITING_SLACK`), leaving a snapshot at
`state/<run_id>/NN_awaiting_slack.json` with `status: awaiting_slack` and a `pending_slack.message_ts`.

**In Slack:** the bot posts the numbered questions into `LOOP_ORCHESTRATOR_SLACK_CHANNEL`. **Reply in that
message's thread:**
```
1: Prioritize durability — persist to a replicated store; drop the memory-only constraint.
```
(Bare text is accepted only if exactly one question is open; otherwise number every line.)

**Expected:** the daemon logs the `events_api` receipt, `find_paused_snapshot_by_slack_thread` matches
the thread, `dispatch_resume` runs (`resume starting … resume finished`), and the bot posts the outcome
back into the thread (`Run completed.` / a failure reason / `More questions came up — see the new
thread…` if it re-escalates).

---

## 4. Evidence to capture (the point of the smoke)

- [ ] Initial run **exited 5** and wrote `state/<run_id>/*_awaiting_slack.json`.
- [ ] The **escalation post** appeared in the channel (note its `message_ts` == the snapshot's
      `pending_slack.message_ts`).
- [ ] Daemon logs show the **`events_api` message event was received and not dropped** — this is the
      real-payload-shape check (`payload["event"]["channel"]/thread_ts/text`). **If the reply is
      silently ignored, the payload-shape assumption is wrong — that is the headline finding.**
- [ ] The **correlation matched** and the run **resumed to a terminal state**.
- [ ] The **outcome post** landed in the thread.

**Cheap negative checks (high value, do them in the same session):**
- [ ] A reply in a **different channel** → dropped, no resume (FD3 channel guard on `message` events).
- [ ] The **bot's own** escalation/outcome post → not parsed as an answer (no self-trigger loop).
- [ ] A **garbage** reply (`hello`) against a multi-question pause → the "couldn't parse — number your
      lines" hint is posted, no resume.
- [ ] A **second** reply to the same thread **after** the resume finished → no double-resume (the
      snapshot is no longer `awaiting_slack`).

---

## 5. Teardown + record

- `Ctrl-C` (or `SIGTERM`) the daemon.
- Optionally delete the scratch `state/<run_id>/` dir.
- Record the discharge (or any finding) back in **BL-37** in `docs/backlog.md`: pass/fail per checklist
  item, and promote the payload-shape result to a `src/` finding if the daemon dropped a real reply.

## Likely failure modes (and what they mean)

| Symptom | Most likely cause |
| --- | --- |
| No `message` event ever reaches the daemon | `message.channels` not subscribed, or `channels:history` scope missing / app not reinstalled |
| Daemon logs the event but drops it before resume | Real `events_api` payload shape ≠ `daemon.py`'s field paths (**the key finding**), or the daemon isn't running from the checkout where the run wrote its snapshot |
| Reply parsed but resume crashes | A real fold-back bug surfacing only under live conditions |
| Run never pauses (exits 0) | The requirements didn't force a human escalation — sharpen per §2 (see BL-7) |
