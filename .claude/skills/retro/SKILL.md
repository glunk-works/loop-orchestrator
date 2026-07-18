---
name: retro
description: A session-end (or on-demand) retrospective on HOW WE WORKED — mine the live session for friction that RECURRED or cost real rework, then route each finding to its existing home (a backlog BL item, a memory, or a small skill/doc edit). High signal bar; no speculative suggestions, no new parallel doc, no gratuitous new personas. Run at the end of a working session or when asked to look for workflow improvements. NOT for code diffs (that is /critic-gate) or prose-vs-code drift (that is the docs-consistency subagent).
---

# /retro — retrospective on the workflow (route findings, don't duplicate)

Goal: turn a working session's friction into durable improvement **consistently** — not only
when the human happens to ask. This audits the layer nothing else does: **how we worked** —
session mechanics, recurring toil, claims that overreached, manual steps a skill already
covers. (`/critic-gate` + `architect` audit code; `docs-consistency` audits prose-vs-code; the
backlog holds product/infra defects. None look at the working relationship.) It exists to
**reduce** friction — so it must not become a friction generator.

## When to run
- At the end of a working session, before `/handoff` or `/archive-sprint` (optional, never a gate).
- On demand — "look for improvements" / "review how that went."
- **NOT automatically every session.** Most sessions yield nothing worth recording, and
  auto-firing is itself friction.

## The signal bar (apply ruthlessly — this IS the value)
Surface a finding **only** if it **recurred** or **cost real time/rework** this session. A
one-off, or a "could be marginally nicer," is noise — drop it. The model for a good finding is
the backlog's own "found live during X" items and the feedback memories: concrete, caused by
something that actually happened, worth the cost of recording.

Explicitly reject:
- **Speculative / hypothetical** improvements ("we could add X someday").
- **New personas/subagents** — the default answer is **no**. The catalog is already rich and
  every added agent adds friction; propose one only for a real, *repeated* task with no owner.
- Anything **already decided** — see step 1.

## Steps

1. **Read what's already decided FIRST — so you never re-propose it.** Skim `docs/backlog.md`'s
   Index + any owner-deferred decisions (BL items marked "owner's call" / "deferred"), the
   roadmap's NEXT ACTION, and `MEMORY.md`. A "finding" that is already an open BL item, an
   owner-deferred decision, or a standing memory is **not** a finding — at most add a one-line
   "confirmed again (date/PR)" to the existing item if that adds signal. This is the anti-noise
   step; skipping it turns a retro into a re-litigation.

2. **Mine THIS session for friction.** Walk the actual exchange and list every point where a
   step cost more than it should have: a manual workaround, a re-diagnosis, a correction the
   human had to make, a thing done by hand that a skill already covers, a claim that
   overreached. Tie each to the **concrete moment**, not a general worry. Rank most-costly first.

3. **Filter through the signal bar.** Drop the one-offs and speculation. What survives is real.

4. **Route each survivor to its existing home — never a new standing doc:**
   - **Recurring workflow defect / infra idea** → a **backlog BL item** (or a "confirmed again"
     note on an existing one), in the backlog's shape (found-live-during-X · why · shape · related).
   - **A how-I-should-work correction or a confirmed-good approach** → a **memory**
     (`feedback`/`user` type; include the why + how-to-apply). Update an existing memory rather
     than duplicate; add its one-line index entry to `MEMORY.md`.
   - **A small mechanical fix** (a skill step, a doc line) → **do it** as a skill/doc edit on a
     branch → PR, if cheap and unambiguous; otherwise file it.
   - **A genuine judgment call for the owner** → **surface it, don't resolve it**
     (`feedback_dont_preempt_tightening`).

5. **Implement the cheap; propose the rest.** Land the unambiguous mechanical fixes; present the
   judgment calls with a recommendation and let the owner pick. Report **where each finding was
   routed** (BL-N / memory / PR / deferred) — the git + PR + backlog history *is* the record;
   there is deliberately no retro log to maintain (BL-25).

## Guardrails
- **Route, don't duplicate.** Every finding lands in the backlog, a memory, or a skill/doc edit
  — never a new standing document. If it fits no existing register, that is a signal it is noise.
- **Default answer to "new persona?" is no** (a real, repeated, ownerless task is the only yes).
- **Never resolve an owner-deferred decision** as a retro finding — re-surface at most.
- **Meta, not code/product.** Code diff → `/critic-gate`; prose-vs-code drift →
  `docs-consistency` subagent; product/infra defect → a BL item. `/retro` is the working
  relationship and the session mechanics.
- **Less friction is the objective.** If a proposed "improvement" adds a step, a doc, or an
  agent without removing more than it adds, it fails its own test — drop it.
