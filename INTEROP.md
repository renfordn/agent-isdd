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

`tasks.md`'s per-task `Depends On` field is deliberately not part of this mapping: the handoff
spawns one Slice Spec (one task/phase) at a time, and phase ordering already carries the
sequencing signal, so there is no cross-task ordering for `agent-tdd` to resolve on its side —
assessed and decided against, not left unaddressed.

This is a **one-directional handoff**: agent-isdd does not resume, monitor, or drive
`agent-TDD` past the initial spawn. Whatever context resumes `agent-TDD` after its
Green→Refactor review pause (via `SendMessage` to its agent id, per `agent-tdd`'s own contract)
is outside agent-isdd's scope once the handoff is made.

**Availability check**: unlike `agent-nelly`, which is checked eagerly at `before-requirements`
and cached in `workflow-state.json` because it is used throughout the workflow, `agent-tdd` is
only needed once — at the handoff. Check availability inline at that point by scanning the
current session's `<system-reminder>` agent-types block for the string `agent-tdd:agent-TDD`.
No caching or `workflow-state.json` field is needed. If absent, pause with a concrete,
actionable message (e.g. "agent-tdd is not installed in this session — install it before
requesting implementation") rather than attempting the work internally.

## ← agent-tdd / code-reviewer (rollback request)

Sometimes `agent-tdd`'s Green→Refactor review pause (or `code-reviewer`) discovers that the
*task* itself — not just the implementation — was wrong. There is no cross-plugin IPC to build
a live push channel for this, so the return path is a documented marker convention plus a
check `agent-isdd` performs on its own re-entry, not agent-isdd reaching into `agent-tdd`'s
active loop. Two genuinely different marker formats feed two different paths below — this used
to be documented as one marker with two delivery paths, which was wrong: `agent-tdd` never emits
SDD-specific vocabulary (see its own `INTEROP.md`), so it cannot literally emit the human-relay
marker below itself. That was a real gap, not just a documentation gap — closed by giving
`agent-tdd` its own generic marker instead of assuming it would speak agent-isdd's.

**Automatic path** (agent-tdd's own generic signal): `agent-tdd`'s **Plan Validity Flag** (see
`agent-tdd/INTEROP.md`'s section of the same name) is a caller-agnostic marker —
`<!--AGENT-TDD-PLAN-FLAG:reason="..."-->` — with no target phase, since `agent-tdd` has no
concept of agent-isdd's phase vocabulary. When `agent-tdd:agent-TDD`'s spawn report contains it,
`hooks/subagent_report.py`'s `SubagentStop` handler recognizes it (independently of its normal
narrative-report capture, which excludes implementation-phase reports otherwise), defaults the
rewind target to `Requirements` — per `references/rollback-guide.md`'s existing "Which target
phase to name" policy: an unclear or absent target defaults to the more conservative (earlier)
phase, since it's always safer to re-confirm a phase that may have been fine than to skip past
one that actually needs revision — and writes `rollback_pending` to `workflow-state.json` plus a
`Pending Rollback Request` line to `workflow-state.md`, with the reason text tagged so a later
reader (or `workflow-manager`'s own "Rollback Request Intake," which reads the reason and can
re-target forward per its documented rule) knows `Requirements` was defaulted, not derived from
the reason. The next `before-continue` hook checks for it first and routes into the Rewind
Contract.

**Human-relay path** (agent-isdd's own vocabulary, for a human relaying a finding): a human (or
whichever context is driving) who already knows agent-isdd's phase names can paste this marker
directly into a message re-entering agent-isdd:

```
<!--SDD-ROLLBACK-REQUEST: target=<Requirements|Design|Tasks> reason="..."-->
```

`before-continue` recognizes it in user input the same way, when present — this is the path for
`code-reviewer`'s findings, or any `agent-tdd` resume happening via `SendMessage` in a session
agent-isdd isn't part of, since neither has an automatic hook of its own. For step-by-step
instructions on both paths, see [`references/rollback-guide.md`](references/rollback-guide.md).

Do not treat either path as a fully automatic guarantee on its own: the automatic path only
fires when `agent-tdd` actually raises a Plan Validity Flag on its *initial* spawn report (not
on a later `SendMessage` resume, which this hook does not observe), and only ever targets
`Requirements` by default — human-relay remains the only path with an explicit target, and the
only path for `code-reviewer` altogether.

## → code-reviewer (review gate)

agent-isdd never invokes `code-reviewer` directly. It is `agent-tdd`'s responsibility (per
`agent-tdd`'s own `INTEROP.md`) to arrange the review gate with whichever context is driving
implementation after the handoff above.

## → agent-ux (UX rendering)

At every phase transition, section-confirmation checkpoint, review-dashboard threshold, and
out-of-scope-task flag, `agent-isdd` delegates to `agent-ux:ux-agent` instead of an in-process
agent, constructing the UX Event Envelope (`caller: agent-isdd`, `event_type`, `phase_state`,
`delta`, `artifact_path`) defined in `agent-ux`'s own `INTEROP.md` — that document is the
authoritative schema (envelope shape, the five per-`event_type` delta shapes, and the
pull-over-push invariant); this section only states how `agent-isdd` uses it, not a duplicate
definition.

`agent-ux:ux-agent` is a **soft dependency**, same pattern as `agent-nelly` below: if it is not
installed or otherwise unreachable, `agent-isdd` catches the missing-plugin condition, surfaces
one plain notice for the session (not one per event), and continues without blocking — see
`agent-ux`'s `INTEROP.md` "Unavailability and fallback contract" section for the full generic
contract (including its own internal fallback when a specific rendering tool like `Artifact` is
unavailable), referenced here by name rather than restated.

The `TaskCreate`/`TaskUpdate`/`TaskList` checklist is not part of this delegation — `agent-ux`'s
isolated subagent context cannot reach deferred tools, so the calling skill renders/refreshes the
checklist directly, unchanged from today's local-agent behavior.

## → agent-nelly (memory)

Before starting or continuing meaningful phase work, `agent-isdd` delegates to
`agent-nelly:nelly-orchestrator` for a goal-aware brief — nelly's four output sections are
`Intent`, `Relevant entries`, `Intent alignment`, and `Written`; agent-isdd uses `Intent` to
seed/check the feature's `Goal` field, and `Intent alignment` as the divergence signal — rather
than reading `~/.claude/sdd-memory/` cross-feature index files directly. If `agent-nelly` is
unavailable, agent-isdd surfaces one plain notice and continues without the Intent-alignment
check — never a hard dependency.

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

**Write-back during spec phases**: at each `after-*` hook (`after-requirements`,
`after-design`, `after-tasks`), when `agent_nelly_available` is `true`, agent-isdd calls
`agent-nelly:nelly-orchestrator` with a `new facts` batch containing any project-level
discoveries worth persisting across future sessions — for example: interface assumptions
confirmed or denied during requirements, coverage gaps or unexpected interfaces found during
design research, risk flags raised by `tdd-planner`. The criterion is "would a future
conversation benefit from knowing this independently of this feature's own artifacts?" — ephemeral
workflow state (user confirmed step N, phase advanced) never qualifies. Choose the call shape by
content: a positive discovery (a confirmed interface, a constraint, a risk) is a `new fact`/
`new facts` batch; a discovery that a specific approach was tried and rejected (a design
contradicted by a security finding, a task slice that had to be abandoned and resliced once the
code was actually read) is an `error lesson` instead — a future session benefits more from being
warned off the dead end than from a fact restating the final state. If the call fails or
nelly is unavailable, log a one-line note in `recap.md` and continue — it is never a blocking
condition. agent-nelly requires no changes to support this: `new facts` is already part of its
standard call contract (see `agent-nelly`'s `INTEROP.md`).
