# Interop: agent-isdd

This plugin owns Requirements → Design → Tasks only. It hands off to three sibling plugins
rather than owning their work. This document is the authoritative description of each boundary,
for both agent-isdd's own maintainers and the sibling plugins' maintainers to cross-check.

> Status: skeleton written in Phase 1 of the `agent-isdd` scope refactor; the concrete Slice
> Spec mapping below is implemented and finalized in Phase 3. See
> `~/.claude/sdd-memory/users-jay-nelson-codebase-ai-plugins-claude-agent-isdd/spec/2026-08-12-isdd-plugin-scope-refactor/`
> for the full requirements/design/tasks this repo was built from.

## → agent-tdd (implementation)

At the end of Tasks, once the Task Readiness Checklist passes and implementation is requested,
`agent-isdd` constructs a **Slice Spec** from the approved `tasks.md`/`design.md` and spawns
`agent-tdd:agent-TDD` directly (via the `Agent` tool), or `agent-tdd:test-author` first for
`high-risk`-tier slices.

Field mapping (agent-isdd's artifact field → agent-tdd's expected Slice Spec field, per
`agent-tdd`'s own `agents/agent-TDD.md` / `agents/test-author.md` / `INTEROP.md`):

| agent-isdd source | agent-tdd field |
|---|---|
| `tasks.md` phase's `Objective` + `Ordered Steps` | Task description |
| `tasks.md` phase's `Test Intent` | Test Intent / acceptance criteria |
| `tasks.md` phase's `Risk Tier` | Risk Tier |
| `design.md`'s `Data Contracts And Interfaces` section (matching module/interface) | Data Contracts And Interfaces |
| `agent-nelly` pre-slice brief, if available | Pre-Slice Brief |
| (not set — default) | Review handoff mode (agent-tdd defaults to "pause for caller-driven review") |

This is a **one-directional handoff**: agent-isdd does not resume, monitor, or drive
`agent-TDD` past the initial spawn. Whatever context resumes `agent-TDD` after its
Green→Refactor review pause (via `SendMessage` to its agent id, per `agent-tdd`'s own contract)
is outside agent-isdd's scope once the handoff is made.

## ← agent-tdd / code-reviewer (rollback request)

Sometimes `agent-tdd`'s Green→Refactor review pause (or `code-reviewer`) discovers that the
*task* itself — not just the implementation — was wrong. There is no cross-plugin IPC to build
a live push channel for this, so the return path is a documented marker convention plus a
check `agent-isdd` performs on its own re-entry, not agent-isdd reaching into `agent-tdd`'s
active loop.

**Marker format**, emitted as a line in the reporting agent's final report:

```
<!--SDD-ROLLBACK-REQUEST: target=<Requirements|Design|Tasks> reason="..."-->
```

**Automatic path**: when `agent-tdd:agent-TDD`'s (or `agent-tdd:test-author`'s) *initial* spawn
report contains this marker, `hooks/subagent_report.py`'s `SubagentStop` handler recognizes it
(independently of its normal narrative-report capture, which explicitly excludes
implementation-phase reports) and writes `rollback_pending` to `workflow-state.json` plus a
`Pending Rollback Request` line to `workflow-state.md`. The next `before-continue` hook
(`workflow-manager`'s "Rollback Request Intake") checks for it first and routes into the
Rewind Contract automatically.

**Human-relay path**: this only works when agent-isdd is present in the same session as the
`SubagentStop` event. `code-reviewer`'s findings, and any `agent-tdd` resume happening via
`SendMessage` in a session agent-isdd isn't part of, have no automatic hook — the marker text
is meant to be relayed by a human (or by whichever context is driving) directly into a message
to agent-isdd, which `before-continue` also recognizes when present in user input.

Do not treat this as a fully automatic guarantee: it is automatic exactly where a
`SubagentStop` can observe the report, and human-relay everywhere else.

## → code-reviewer (review gate)

agent-isdd never invokes `code-reviewer` directly. It is `agent-tdd`'s responsibility (per
`agent-tdd`'s own `INTEROP.md`) to arrange the review gate with whichever context is driving
implementation after the handoff above.

## → agent-nelly (memory)

Before starting or continuing meaningful phase work, `agent-isdd` delegates to
`agent-nelly:nelly-orchestrator` for a goal-aware brief (Goal, prior decisions, open risks,
goal-alignment check) rather than reading `~/.claude/sdd-memory/` cross-feature index files
directly. If `agent-nelly` is unavailable, agent-isdd surfaces one plain notice and continues
without the goal-alignment check — never a hard dependency.

agent-isdd still owns writing its own per-feature `spec/` artifacts
(`workflow-state.md`/`.json`, `requirements.md`, `design.md`, `tasks.md`, `recap.md`) under
`~/.claude/sdd-memory/<project-slug>/spec/<feature-slug>/` directly — that scaffolding
(`hooks/sdd_memory.py`) is not part of what `agent-nelly` owns.

Within a continuous stretch of phase work, agent-isdd does not re-call
`agent-nelly:nelly-orchestrator` on every step once a brief has already been fetched and is
still visible in context — it reuses the in-session brief instead. The full re-fetch-trigger
convention lives in `skills/spec-driven-development/SKILL.md`'s Goal-Aware Memory section (this
is a documentation pointer, not a duplicate definition). `workflow-state.json` is intentionally
unchanged by this dedup convention — it carries no brief-caching field.
