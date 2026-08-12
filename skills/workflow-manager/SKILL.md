---
name: workflow-manager
description: "[Internal — use /isdd instead] Resolve workflow state deterministically, decide start or continue behavior, repair stale state, scaffold per-feature artifacts, and control phase transitions through Requirements/Design/Tasks and the handoff to implementation."
---

# Workflow Manager

## Purpose

Use this skill internally whenever the SDD workflow needs to:
- start a new feature workflow (including scaffolding its folder structure)
- continue an existing workflow
- infer the active phase
- decide whether to auto-advance or pause
- repair stale or contradictory workflow artifacts
- hand off to implementation

This skill is not the main user-facing prompt. It exists to make the top-level
`spec-driven-development` workflow reliable. It also folds in what used to be a separate
`artifact-scaffolder` skill — folder/file scaffolding is deterministic bookkeeping, the same
category of work as state resolution, not creative authoring, so there's no reason for a model
to route to a second skill for it.

## Inputs (Decision Order)

Resolve inputs in this priority order:

1. `agent-nelly:nelly-orchestrator`'s stored Intent (via the Availability Check gate — see
   "Goal Field Contract" below)
2. `workflow-state.md`
3. `workflow-state.json`
4. unresolved blockers or confirmation checkpoints
5. phase files (`Status` sections)
6. `recap.md`

When available, agent-nelly's Intent outranks all workflow artifacts: cross-project facts and
the project's Intent constrain how every lower-priority input is interpreted, but it never
itself encodes phase/stage state — that always comes from `workflow-state.md`/
`workflow-state.json`. When unavailable (per the Availability Check), this input is skipped
entirely and resolution starts from `workflow-state.md`.

### Goal Field Contract

- Source of truth for this feature's `Goal`: `workflow-state.md`'s own `Goal` field, one line
  per feature — sdd owns and writes this field directly.
- That field is seeded from, and alignment-checked against, `agent-nelly:nelly-orchestrator`'s
  stored `Intent` — one line per *project*, not per-feature (see design.md's "Intent → Goal
  Mapping"). Intent is coarser-grained than Goal: it captures what the project is for, while
  Goal captures what this specific feature is for, expected to be consistent with, but not
  identical to, the project's Intent.
- On `start`, if the Availability Check (below) found `agent-nelly:nelly-orchestrator` available,
  call it (via the `Agent` tool, `subagent_type: agent-nelly:nelly-orchestrator`) to read the
  stored Intent. If Intent is more specific than "not yet captured," seed the new
  `workflow-state.md`'s `Goal` field from it; otherwise ask the user for the feature's Goal as
  before (a feature's Goal is not always identical to its problem statement). If unavailable,
  always ask the user — there is no Intent to seed from.
- On every `before-continue`, if available, call `agent-nelly:nelly-orchestrator` with a
  one-line description of the current phase/task for an Intent-alignment check. If it flags a
  divergent Intent, treat that as a pause-worthy condition (see Pause Rules) rather than
  something to note and continue past. If unavailable, skip this check entirely — no pause, no
  error, per the Availability Check's graceful-degradation rule.
- `workflow-state.md`'s `Goal` field is always authoritative for this feature once seeded —
  agent-nelly's Intent is a project-level alignment signal, not a per-feature value to
  repair `workflow-state.md` against on every disagreement; only an explicit divergence flag
  from the alignment check is pause-worthy, per the paragraph above.

### Availability Check

- At the `before-requirements` hook (workflow start) and the `before-continue` hook (workflow
  resume), check the current session's agent-types listing — the `<system-reminder>` block that
  enumerates "Available agent types for the Agent tool" — for the string
  `agent-nelly:nelly-orchestrator`.
- Cache the boolean result in `workflow-state.json`'s `agent_nelly_available` field so later
  steps in the same hook (and later hooks) don't need to re-inspect the listing.
- If unavailable, surface one plain notice to the user and continue the workflow without the
  Intent-alignment check — this is graceful degradation, never a blocking condition.

### `workflow-state.md` Vs `workflow-state.json` Conflict Resolution

Dual-written on every phase transition. They must agree. When they disagree:

- `workflow-state.md` is always authoritative.
- Repair `workflow-state.json` in place so its fields match `workflow-state.md`.
- Log the repair as a one-line note in `recap.md`.
- Never silently accept `workflow-state.json` as correct when it disagrees; never skip logging.

## Scaffolding (folded from the former `artifact-scaffolder` skill)

Per-feature artifacts are plugin-generated state, not source — they live under the project's
central SDD memory directory (`~/.claude/sdd-memory/<project-slug>/`), never inside the repo.
Resolve (and create, if missing) a feature's folder with
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/sdd_memory.py" --spec-path <YYYY-MM-DD-feature-slug>`
rather than hand-building the path — this also rejects unsafe slugs. Reads and writes under the
memory directory are auto-approved by `hooks/memory_permission.py`.

On `start`, create the per-feature structure; on later phases, update files in place rather
than recreating them:

```text
<sdd-memory-dir>/
  spec/
    <YYYY-MM-DD-feature-slug>/
      workflow-state.md
      workflow-state.json
      requirements/requirements.md
      design/design.md
      tasks/tasks.md
      recap/recap.md
```

Rules:
- one feature folder per feature, named with local start date plus slug
- use the exact template bodies from `references/artifact-templates.md` and
  `references/workflow-state.template.json`
- preserve section order so later agents can rely on stable parsing
- `workflow-state.json` is scaffolded together with `workflow-state.md` every time the latter
  is created or updated (see the field schema in `references/workflow-state.template.json`)

## Required Decisions

For every invocation, determine: active feature folder, requested action (`start`, `continue`,
`pause`, `handoff`, `complete`), authoritative current phase, workflow status, pause reason if
any, next action.

## Phase Completion Evaluation

For `Requirements`, `Design`, and `Tasks`, evaluate completion against explicit pass/fail
checklists (`references/artifact-templates.md`), not broad narrative judgment. A phase passes
only when every required item is satisfied, fails when any required item is unchecked,
contradicted, or blocked, and is `blocked` when completion depends on user confirmation, missing
information, or unresolved contradictions.

## Lifecycle Hooks

Ownership note: this skill defines the field-update contract below — which fields change and to
what values, at each hook. It does not claim to be the sole actor performing the write: whichever
thread is currently executing (the top-level `spec-driven-development` orchestrator mid-workflow,
or `workflow-manager` itself when invoked standalone, e.g. via `/isdd-status`) performs the actual
file write, using this contract. `spec-driven-development`'s own references to updating
`workflow-state.md`/`recap.md` mean "per this contract," not a separate, competing set of rules.

Model enforcement through workflow lifecycle hooks, not plugin manifest hooks:
`before-continue`, `before-requirements`, `after-requirements`, `before-design`, `after-design`,
`after-tasks`. Each hook must allow, update state and continue, or pause with a concrete reason.
Every hook writes `Last Hook Run`, `Last Hook Outcome`, `Last Hook Decision`, `Hook Notes`.

### `before-continue`

Resolve the active feature folder, read `workflow-state.md`, check for a pending rollback
request first (see "Rollback Request Intake" below — this takes priority over everything else
in this hook), call `agent-nelly:nelly-orchestrator` (if available, per the Availability Check)
for the Intent-alignment check, detect stale/contradictory artifacts, repair if safe, decide
the next action, write the result.

**Verification Step**: before reporting this hook's decision as final, confirm `recap.md` and
`hook_history` actually reflect it — if `state_consistency_check.py` already repaired drift for
this write (see its `hook_history` entry), trust that as evidence rather than re-deriving it;
otherwise check directly. If `recap.md` didn't change for a claimed state-changing decision,
pause instead of continuing.

### `before-requirements`

Ensure artifacts exist (scaffold if not), initialize/repair `workflow-state.md` including its
`Goal` field (seeded via `agent-nelly:nelly-orchestrator`, if available, per the Availability
Check), decide `requirements-agent`'s entry mode (author from scratch vs. review an existing
draft), confirm no invalid earlier phase is being skipped, write the result.

### `after-requirements`

Evaluate the `Requirements` completion checklist, update `workflow-state.md` and `recap.md`,
decide advance-to-Design vs. pause, record the outcome.

**Verification Step**: before advancing, confirm `recap.md` actually changed and a
`hook_history` entry exists for this transition — a script can verify the JSON/MD fields agree
(`state_consistency_check.py`), but only this hook can judge whether `recap.md`'s content is
meaningful, not just present. If either check fails, pause rather than advance.

### `before-design`

Confirm Requirements are approved, no blocking gap remains, no confirmation checkpoint is open,
enter native plan mode (see "Native Plan Mode Gate"), write the result.

### `after-design`

Evaluate the `Design` completion checklist, update `workflow-state.md` and `recap.md`, decide
advance-to-Tasks vs. pause, record the outcome.

**Verification Step**: same check as `after-requirements` — confirm `recap.md` changed and a
`hook_history` entry exists before advancing; pause otherwise.

### `after-tasks`

Evaluate the `Tasks` completion checklist, update `workflow-state.md` and `recap.md`, decide
handoff, pause-for-implementation-request, or pause-for-blocker, record the outcome. If the
checklist passes and handoff is the decision, exit native plan mode (see "Native Plan Mode Gate")
before setting `Current Phase: Implementation`.

**Verification Step**: same `recap.md`/`hook_history` check as the other `after-*` hooks. When
the decision is `handoff`, additionally rely on `hooks/slice_spec_gate.py` — it hard-denies the
`agent-tdd` spawn itself if the constructed Slice Spec is missing a required field, so this
hook does not need to re-verify Slice Spec completeness by hand.

## Start Rules

Choose `start` when no matching feature folder exists, the user explicitly asks to start a new
workflow, or an existing workflow should not be reused safely. When starting: derive the slug,
scaffold the structure, capture the Goal via `agent-nelly:nelly-orchestrator` (if available, per
the Availability Check) or by asking the user, initialize `workflow-state.md` and `recap.md`,
route into `requirements-agent`.

## Continue Rules

Choose `continue` when a matching feature folder exists, status is `In Progress`, and the active
phase is not complete. When continuing: read `workflow-state.md`, validate against phase
artifacts, repair if stale, evaluate completion checklists, continue from the earliest
incomplete or blocked phase.

## Pause Rules

Choose `pause` when: a blocker exists, user confirmation is required, active feature resolution
is ambiguous, a phase gate fails, any completion checklist fails, or `agent-nelly:nelly-
orchestrator` raises an unresolved Intent-alignment flag (only checked when available). When
pausing: keep `Current Phase` unchanged, set `Workflow Status` precisely, set `Pause Reason`,
set a concrete `Next Action`.

## Native Plan Mode Gate

The Design and Tasks phases *are* the implementation plan — codebase research, architecture,
task breakdown — culminating in the moment code is about to be written. That maps directly onto
the harness's own plan mode, so this workflow rides it instead of only gating through
conversational confirmation:

- On `before-design`, call `EnterPlanMode` before routing into `design-author`. Skip the call (do
  not error or pause) if plan mode is already active for this session — never enter twice.
- Stay in plan mode through `Design` and `Tasks`. Both phases already only touch markdown
  (`design.md`, `tasks.md`), which is exactly what plan mode expects — no separate discipline is
  needed here beyond what those phases already do.
- Before calling `ExitPlanMode` on `after-tasks`, write the finalized `design.md` + `tasks.md`
  content (or a faithful summary of both) to the plan file the harness specified when plan mode
  was entered, so the user's native approval screen reflects the actual plan rather than an empty
  or stale file. This is in addition to, not a replacement for, the repo-persisted `design.md`
  and `tasks.md` — the plan file is scratch for the approval UI, the repo files remain the
  durable artifacts.
- Only call `ExitPlanMode` once the `Tasks` checklist passes per "Phase Pass/Fail Rules" — the
  same gate `Handoff Rules` already requires, not a separate or looser one.
- If `EnterPlanMode`/`ExitPlanMode` aren't available on this host, or the call fails for a reason
  unrelated to the checklist (host declines, tool not present), fall back silently to the
  existing conversational Design Gate / Task Readiness confirmation already required elsewhere in
  this workflow — never block phase progress on plan-mode availability.
- A user-declined `EnterPlanMode` is a pause condition like any other missing confirmation (see
  Pause Rules), not a reason to proceed without it.

## Handoff Rules

Choose `handoff` when `Tasks` are ready, implementation was requested, no unresolved blockers or
confirmation checkpoints remain, and the `Tasks` checklist passes. Set `Current Phase:
Implementation`, `Current Owner: User`, `Workflow Status: In Progress`, then let
`spec-driven-development`'s "Implementation Handoff" step build the Slice Spec and spawn
`agent-tdd:agent-TDD` — a single, one-directional handoff (see `INTEROP.md`). Once that spawn
returns its handoff report, set `Workflow Status: Complete`; this skill tracks no further
implementation-stage state.

## Complete Rules

Choose `complete` when planning finished without an implementation request, or implementation
is complete with no further phase work. Set `Workflow Status: Complete`, `Pause Reason: None`,
`Next Action: None`.

## Phase Pass/Fail Rules

### Requirements

Pass only when: `Approval Checkpoint` is fully satisfied, required EARS fields are present,
`Open Gaps` has no unresolved blocking item, `Phase Completion` is fully satisfied, `State` is
`Approved`. Fail when any checkpoint item is incomplete, EARS requirements are missing or
materially weak, or unresolved ambiguity remains.

### Design

Pass only when: `Phase Decision` is fully satisfied, requirement coverage is explicit,
interfaces/touchpoints/validation strategy are present (grounded in `planning-agent`'s
findings, not guessed), `Phase Completion` is fully satisfied, `State` is `Approved`. Fail when
any phase decision item is incomplete, design contradicts approved requirements, or validation
strategy is weak or absent.

### Tasks

Pass only when: `Task Readiness Checklist` is fully satisfied, at least one concrete
implementation phase exists, tasks are sliced safely for TDD, confirmation blockers are
resolved, `State` is `Ready For Implementation` or `Complete`. Fail when slices are oversized,
validation targets are missing, test intent is missing, or required confirmation remains open.

## State Repair Rules

Treat `workflow-state.md` as stale when: a later phase file has a newer `Last Updated` with an
approved state, the recorded current phase is earlier than the newest approved phase, the
stored pause reason doesn't match the actual blocker, or the stored next action doesn't match
the earliest incomplete phase. When repairing: prefer the newest internally consistent
artifacts, update `workflow-state.md`, note the repair in `recap.md`, never silently discard
unresolved contradictions, keep phase pass/fail status aligned with the repaired state.

A `workflow-state.json` missing the `agent_nelly_available` field (from an in-flight feature
whose file predates this field) is not a staleness/error condition — treat it as "not yet
checked" and let the next `before-continue` hook populate it via the Availability Check.

## Rewind Contract

`commands/isdd-rewind.md` delegates all rewind state-mutation logic to this contract.

A rewind request names a target phase (`Requirements`, `Design`, or `Tasks`) earlier than or
equal to the current `Current Phase`. On a valid rewind:

- Set `Current Phase` (both files) backward to the target phase.
- Set `Workflow Status`/`phase_state` for re-entry (typically `In Progress`); clear
  `Pause Reason`/`pause_reason` only if the pause was specific to the phase being left.
- Do not clear, reset, or overwrite the `Status`/blocked fields of any later phase — rewinding
  only moves the *current* pointer, it does not retroactively resolve later-phase state.
- Log the rewind (from, to, actor, timestamp) in `recap.md` and as a `hook_history` entry.
- If the target is later than `Current Phase` or doesn't exist, refuse and pause with a
  concrete reason.

## Rollback Request Intake

Part of `before-continue` (see above) — checked first, before anything else in that hook.

A rollback request reaches agent-isdd two ways, per `INTEROP.md`'s "← agent-tdd / code-reviewer
(rollback request)" section: automatically, via `rollback_pending` in `workflow-state.json`
(written by `hooks/subagent_report.py` when it recognizes the marker on `agent-tdd`'s initial
spawn report), or via human-relay, when the marker text appears directly in the user's message
re-entering agent-isdd.

On either form:

- Determine the target phase from the request. If it doesn't clearly map to what changed,
  default to the more conservative (earlier) phase rather than guessing narrowly.
- Invoke the existing Rewind Contract at that target phase — this is the only mutation path;
  do not duplicate its state-mutation logic here.
- Clear `rollback_pending` (via `sdd_state.clear_rollback_pending`) once the rewind is applied.
- Log the event in `recap.md` distinctly from a routine rewind — e.g. "Rollback
  (mid-implementation): <from> → <to>, reason: <reason>" rather than the Rewind Contract's
  plain "Rewind: <from> → <to>" phrasing — so a later reader can tell a rollback (triggered by
  an implementation-side finding) apart from a routine user-initiated rewind.
- This applies even when `Workflow Status` is `Complete` — `before-continue` is the standard
  re-entry point regardless of prior status, so a rollback request reopens the workflow at the
  target phase rather than requiring manual state repair.
- **Loop prevention**: if the same target phase is requested twice in a row, pause and surface
  the repetition to the user rather than rewinding again automatically. (This is a new
  convention for agent-isdd, styled after — not shared with — `agent-tdd`'s own "stop after 2
  identical attempts" rule; no loop-prevention convention existed in this plugin before this.)

## Mid-Phase Change Classification

When the user raises a new idea or a differing task while Design or Tasks is the active phase,
classify the change before reacting, reusing the Rewind Contract for its only mutation path:

- Does satisfying the change require editing an **already-approved earlier phase's own
  artifact** — a `requirements.md` EARS/constraint/non-goal for a Design-phase idea, or a
  `design.md` Architecture/Data-Contracts-And-Interfaces section for a Tasks-phase idea? →
  **earlier-phase invalidation** → invoke the Rewind Contract to that phase.
- Does it only require editing the **current phase's own artifact**, staying inside what that
  phase already owns? → **current-phase refinement** → redo the current phase in place; no
  `Current Phase` change.
- If ambiguous, ask exactly one narrow question: "Does this change *what* we're building
  (would require editing `requirements.md`) or *how* we're building it (stays inside
  `design.md`/`tasks.md`)?"
- Always record the classification, its reasoning, and the branch taken in `recap.md`, so a
  later reader can see why a mid-phase change did or didn't trigger a rewind.

## Task Tracker Sync

The breadcrumb is owned by `ux-agent`; the `TaskCreate`/`TaskUpdate`/`TaskList` checklist is not
(`ux-agent`'s isolated subagent context cannot reach deferred tools via `ToolSearch` in this
harness — observed in a past session, not a documented platform guarantee; re-verify if harness
behavior seems to have changed). Call `TaskCreate`/`TaskUpdate`/`TaskList` directly, self-
loaded via `ToolSearch` first. `hooks/phase_task_sync.py` fires a reminder on every
`workflow-state.md`/`tasks.md` write as a backstop — on that reminder, sync the checklist
directly rather than delegating to `ux-agent`.

## Guardrails

- Do not restart a workflow when continuation is safer.
- Do not continue into a later phase when an earlier phase is invalidated.
- Do not hand off to implementation unless tasks are explicitly ready.
- Do not leave `workflow-state.md` stale after a routing decision.
- Do not skip the Goal-field capture on `start`, or the Intent-alignment check on
  `before-continue` when `agent-nelly:nelly-orchestrator` is available.
- Do not scaffold a second, divergent folder structure — always the one canonical layout above.
