---
name: spec-driven-development
description: Orchestrates the intent spec-driven workflow — EARS requirements through design and tasks — with hard phase gates, a visible breadcrumb/checklist UI, and goal-aware memory. Hands off to separate implementation/review/memory plugins.
---

# Spec Driven Development

## Purpose

Use this skill when the user wants one workflow that can:
- generate or review specs
- enforce a spec-driven process with hard phase gates
- research the codebase and produce a testable design and TDD-sized task breakdown
- hand off cleanly to implementation once the spec is approved
- keep visible progress (breadcrumb + checklist) and goal-aware memory throughout

This is the only user-facing entrypoint for the workflow unless the user explicitly asks for a
focused skill by name. It routes work across the companion skills internally:
- `workflow-manager`
- `requirements-agent`
- `design-author`
- `tdd-planner`

It owns Requirements, Design, and Tasks only. Implementation is a separate plugin
(`agent-tdd`), invoked once via a one-directional handoff — this skill never drives the
Red-Green-Refactor loop or the code-review gate itself. See `INTEROP.md` at the repo root for
the full handoff contract.

The user should not need to manually prompt each phase skill in order to move through the
workflow.

## Entry Commands

Support these natural-language intents through this single skill: start the workflow, continue
it, resume this feature's workflow, advance to the next phase, continue from the current phase.
Interpret the request and continue automatically — never ask the user to name another skill
first.

## Workflow Contract

Phase-driven, always in this order: `Requirements` → `Design` → `Tasks` → `Implementation`.
`Recap` is maintained throughout as ongoing memory and handoff context. `workflow-state.md` is
the source of truth for current phase and continuation state. `Implementation` here means "the
Slice Spec handoff to `agent-tdd` has been made" — this skill's own responsibility ends there.

Do not skip forward across phases unless the current phase is complete and not blocked.

## Visible Progress (every phase-transition or status response)

Two distinct rendering paths — use the right one based on whether a phase transition is occurring:

**Phase transitions** (Requirements → Design → Tasks → Implementation, or a restart/rewind):
delegate to `agent-ux:ux-agent` (via the `Agent` tool) with a `phase_transition` event envelope
(`caller: agent-isdd`, `event_type: phase_transition`, `phase_state`) so it can mark a session
chapter and update the spec-canvas Artifact. See `INTEROP.md`'s "→ agent-ux (UX rendering)"
section for the envelope contract and the unavailability fallback. Never drive `Artifact`/
`mark_chapter` directly from this skill — those are `agent-ux:ux-agent`'s job.

**Status responses that are not a phase transition** (formerly `breadcrumb_only` delegations):
render a progress line **inline** — no `Agent` tool call. A one-line string does not warrant a
full subagent spawn. Format:

```
**SDD** Requirements [✓] → Design [▶] → Tasks [·] → Implementation [·]
```

Use `workflow-state.md` to determine each phase's status marker: `✓` approved/complete,
`▶` in progress, `✗` blocked, `·` pending. Emit the line before the rest of the response.

The phase `TaskCreate` checklist is different: ux-agent cannot reach `TaskCreate`/`TaskUpdate`/
`TaskList` from its subagent context (see `agent-ux:ux-agent`). Render/refresh the checklist
**directly from this skill instead**, in the same response: self-load the three
tools via `ToolSearch` (`select:TaskCreate,TaskUpdate,TaskList`) once per session if not already
loaded, call `TaskList` to check for existing items before creating, then `TaskCreate`/
`TaskUpdate` per `agent-ux`'s `references/ux-conventions.md`'s Phase tick list conventions (the
convention itself, driven by the calling skill and not `agent-ux:ux-agent`, is unchanged by the
extraction — only where it's documented moved).

## Goal-Aware Memory

Before starting or continuing meaningful phase work, when agent-nelly is available (per the
Availability Check defined in `workflow-manager/SKILL.md`), delegate to
`agent-nelly:nelly-orchestrator` for a holistic brief (Intent, prior decisions, open risks,
Intent-alignment check) instead of reading `~/.claude/sdd-memory/` files directly. If it flags
an Intent-alignment concern, surface it to the user before proceeding — don't silently continue
past a stated drift.

This skill is the single fetch/delegation point, per continuous stretch of phase work, for the
nelly brief **and** for `planning-agent`/`spec-reviewer` findings still valid from earlier in
that same stretch (e.g. a `planning-agent` finding produced during Design that `tdd-planner`
would otherwise re-request during Tasks). When a brief or finding has already been fetched this
session and is still visible in context, reuse it rather than re-calling
`agent-nelly:nelly-orchestrator`/`planning-agent`/`spec-reviewer` again for the same content.
Re-fetch only when one of these triggers applies — identical rule, same three triggers, now
scoped to a wider set of cached content, not a new or looser rule:

1. No prior brief or finding is visible in context (a new session, or context was compacted
   since the last fetch). Applies identically to a `planning-agent`/`spec-reviewer` finding: if
   it isn't visible, it isn't reusable.
2. A rewind (Rewind Contract) or a Mid-Phase Change Classification happened since the cached
   brief/finding was fetched — both live in `workflow-manager`'s `SKILL.md`. A rewind or
   mid-phase change can invalidate a cached codebase finding exactly as it can invalidate a
   brief, since either can change what "the current design/task" even means.
3. `workflow-manager`'s `before-continue` Intent-alignment check flagged a divergence since the
   cached brief/finding was fetched. When this fires, treat every cached item (brief and any
   `planning-agent`/`spec-reviewer` finding alike) as invalidated, not only the brief — an
   Intent-level divergence is a signal about the whole stretch of work, not brief-specific.

None of the three triggers assumed brief-specific semantics that fail to hold for a
`planning-agent`/`spec-reviewer` finding — re-verified as part of extending this rule's scope,
per design.md's mitigation for the correctness risk this generalization raises.

When delegating into `workflow-manager`, `design-author`, or `tdd-planner`, pass along the
already-fetched brief and any still-valid finding explicitly rather than letting any of them
re-derive or re-fetch on their own; `design-author` and `tdd-planner` check for a still-valid
cached finding before re-delegating to `planning-agent`, mirroring how they already check for a
reusable agent-nelly brief. `workflow-manager`'s own `start`-time Goal-seeding call is a distinct-purpose, always-fresh
call outside this dedup pool — see its Goal Field Contract section; it is never satisfied by
reusing a cached brief. The `before-continue` Intent-alignment check no longer spawns a nelly
subagent — it runs inline against the Intent already in session context (see
`workflow-manager/SKILL.md`'s Goal Field Contract).

## Start Protocol

1. Use `workflow-manager` to identify or derive the feature title and slug, and to scaffold or
   locate the per-feature artifact structure.
2. If `agent-nelly:nelly-orchestrator` is available, call it to read the project's stored
   Intent and seed the feature's `Goal` field in `workflow-state.md` from it when Intent is more
   specific than "not yet captured". Otherwise ask the user for the Goal directly.
3. Initialize `workflow-state.md` with `Current Phase: Requirements` and `recap.md` to match.
4. Route into `requirements-agent`: it interviews from scratch when the input is vague, or
   reviews-and-rewrites when the user hands over an existing ticket/PRD/draft — one skill, two
   entry modes, same gate.
5. After Requirements are approved, continue automatically into `Design` (`design-author`).
6. After Design is approved, continue automatically into `Tasks` (`tdd-planner`).
7. After Tasks are ready, stop with a clear handoff message, or perform the one-directional
   `agent-tdd` handoff (see "Implementation Handoff" below) only if the user asked for
   implementation.

## Continue Protocol

1. Use `workflow-manager` to find the relevant feature folder and resolve state (see its
   Decision Order — `agent-nelly:nelly-orchestrator`'s stored Intent first (when available),
   then `workflow-state.md`, then `workflow-state.json`, then open blockers, then phase files,
   then `recap.md`).
2. Continue from the earliest blocked or incomplete phase; auto-advance through later phases
   whose entry gates are satisfied.
3. Pause only when a gate fails, a confirmation checkpoint is required, or implementation was
   not requested.

Do not restart from Requirements if a later phase is already the active incomplete phase,
unless requirement changes invalidate the design or tasks.

## Internal Routing Rule

Use focused skills internally rather than asking the user to switch prompts:
- `workflow-manager` — orchestration, phase detection, state repair, transitions, scaffolding.
- `requirements-agent` — requirements from scratch or from an existing draft/ticket/PRD.
- `design-author` — design, informed by `planning-agent` research and `agent-nelly:nelly-
  orchestrator` (when available).
- `tdd-planner` — phased execution tasks, also informed by `planning-agent`.

Only expose these skill names when the user explicitly asks which one is being used, wants to
invoke one directly, or a pause message needs to explain which capability produced the output.

## Subagent Delegation

Four capabilities ship as **subagents** (`agents/`) so their bounded work runs in an isolated
context and returns only a conclusion, keeping this orchestrator thread lean across a long
workflow:

- `spec-reviewer` — delegate when `requirements-agent` needs to assess an existing draft before
  rewriting it.
- `tdd-planner` — delegate to generate `tasks.md` once Requirements are approved and Design is
  coherent.
- `planning-agent` — delegate before writing `design.md` or `tasks.md`, for wide-fast then
  deep-focused codebase research.
- `agent-nelly:nelly-orchestrator` — an external peer-plugin subagent, not one of this plugin's
  own `agents/`, invoked the same way (via the `Agent` tool with that literal `subagent_type`
  string), gated by the Availability Check — delegate before any phase starts, when available,
  for a goal-aware brief (Intent, prior decisions, open risks, Intent-alignment check); it is
  the sole writer into agent-nelly's own memory store, which agent-isdd never reads or writes
  directly.
- `agent-ux:ux-agent` — an external peer-plugin subagent, delegate at every **phase transition**
  for chapter markers and the spec-canvas Artifact, via the UX Event Envelope (`caller:
  agent-isdd`, `event_type: phase_transition`, `phase_state`, `delta`, `artifact_path` — see
  `INTEROP.md`'s "→ agent-ux (UX rendering)" section). Status breadcrumbs between transitions
  are rendered inline (see "Visible Progress" above). It does not own the `TaskCreate` checklist
  — see "Task Tracker Sync" below.

Delegation rules:
- Prefer the subagent over inlining these when the task is well-scoped.
- Subagents cannot talk to the user. **You** own every user-facing confirmation checkpoint:
  take a subagent's returned report, surface it, get confirmation, then update
  `workflow-state.md` and `recap.md` yourself — per `workflow-manager`'s field-update contract
  (see its Lifecycle Hooks section), not a separate set of rules.
- `requirements-agent` and `design-author` stay inline for interviewing the user, but delegate
  their bounded sub-tasks (`spec-reviewer` for draft assessment; `planning-agent` for research)
  to subagents rather than doing that work in the main thread.

## Implementation Handoff

Once `Tasks` passes its readiness checklist and implementation is requested, this skill's job
is to build a **Slice Spec** and spawn `agent-tdd:agent-TDD` — a single, one-directional
handoff, not an orchestrated multi-stage loop. See `INTEROP.md` at the repo root for the exact
field mapping (`tasks.md`'s Objective/Ordered Steps/Test Intent/Risk Tier, `design.md`'s Data
Contracts And Interfaces, and an optional `agent-nelly` Pre-Slice Brief).

1. If the slice's Risk Tier is `high-risk`, spawn `agent-tdd:test-author` first with the Task
   description, Test Intent, and Data Contracts And Interfaces. Include its returned test
   file(s) and failure confirmation in the next step's Slice Spec.
2. Spawn `agent-tdd:agent-TDD` with the constructed Slice Spec.
3. Take its returned handoff report, log the handoff in `recap.md`, set
   `Workflow Status: Complete` in `workflow-state.md`.
4. If the report's Handoff Facts field is non-empty and `agent_nelly_available` is `true` in
   `workflow-state.json`, call `agent-nelly:nelly-orchestrator` with those facts as a `new facts`
   batch. One call only — no re-fetch of the brief needed.
5. Do not resume, monitor, or drive `agent-TDD` past this initial spawn — anything after its
   own Green→Refactor review pause is outside this skill's scope.
6. If `agent-tdd` (or `agent-nelly` for the Pre-Slice Brief) is not installed, pause with a
   concrete, actionable message rather than attempting the work internally.

## Requirements Gate

Ready to advance only when: all required fields are present, expressed in EARS format, and no
unresolved ambiguity remains. Minimum content: problem statement, user outcome, constraints,
non-goals, edge cases, success criteria, dependencies.

If any of the above are weak, vague, or missing: refuse to advance, interview the user to fill
the weakest areas first, prioritizing the most ambiguous or highest-risk gaps. If ambiguity
remains after interviewing: stop, return the partial draft, return an explicit gaps list.

## Existing Ticket Or PRD Handling

When the user provides a ticket, PRD, or existing spec, `requirements-agent`'s review mode
handles it: review first, rewrite only the weak sections into EARS format, present the changed
draft, pause for confirmation, and only then treat it as the canonical requirements artifact.
Never treat incoming material as automatically sufficient for phase advancement.

## Phase Gating

Phase gating, auto-advance rules, pause conditions, and state repair are governed entirely by
`workflow-manager` — see its `SKILL.md`.

## Native Plan Mode

`workflow-manager` owns entering native plan mode (`EnterPlanMode`) at `before-design` and
exiting it (`ExitPlanMode`) at `after-tasks` once the `Tasks` checklist passes — see its "Native
Plan Mode Gate" section for the full contract. This stays here in the orchestrator rather than
delegated to `agent-ux:ux-agent` because it is a user-facing approval checkpoint (`agent-ux:ux-agent`
never talks to the user).
Requesting approval this way is in addition to the phase gates above, not instead of them —
`ExitPlanMode` is only ever called once the Tasks checklist has already passed.

## Task Tracker Sync

`tasks.md` is a repo-persisted planning artifact, distinct from the harness's own task tracker.
Call `TaskCreate`/`TaskUpdate`/`TaskList` directly from this skill at every phase transition
(self-loaded via `ToolSearch` first) — see "Visible Progress" above.

## Artifact Convention

Per-feature artifacts are plugin-generated state, not source — they live under the project's
central SDD memory directory (`~/.claude/sdd-memory/<project-slug>/`), not the repo:

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

`workflow-manager` owns scaffolding this structure and keeping it stable across phases. Use the
canonical templates in `references/artifact-templates.md`; keep the same section order unless
the user explicitly asks to change it.

## Writing Style

Structured sections with checklists, concise prose plus bullet lists, for `requirements.md`,
`design.md`, and `recap.md`. For `tasks.md`, optimize for agent handoff: minimal narration,
explicit ordered execution steps, concrete validation steps.
