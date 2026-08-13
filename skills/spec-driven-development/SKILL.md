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

Before doing anything else in a response that transitions or reports phase, delegate to the
`ux-agent` subagent for the breadcrumb line. On an actual phase transition (Requirements →
Design → Tasks → Implementation, or a restart/rewind), tell `ux-agent` so it can also mark a
session chapter — never on a status response that isn't itself a transition. Never hand-roll the
breadcrumb text or drive `Artifact`/`mark_chapter` directly from this skill — that's `ux-agent`'s
job (see `agents/ux-agent.md`).

The phase `TaskCreate` checklist is different: `ux-agent` cannot reach `TaskCreate`/
`TaskUpdate`/`TaskList` from its isolated subagent context (deferred-tool resolution via
`ToolSearch` doesn't reach subagents in this harness — observed in a past session, not a
documented platform guarantee; re-verify if harness behavior seems to have changed). Render/refresh
the checklist **directly from this skill instead**, in the same response: self-load the three
tools via `ToolSearch` (`select:TaskCreate,TaskUpdate,TaskList`) once per session if not already
loaded, call `TaskList` to check for existing items before creating, then `TaskCreate`/
`TaskUpdate` per `references/ux-conventions.md`'s Phase tick list conventions.

## Goal-Aware Memory

Before starting or continuing meaningful phase work, if `agent-nelly:nelly-orchestrator` is
available (per `workflow-manager`'s Availability Check — cached in `workflow-state.json`'s
`agent_nelly_available` field), delegate to it for a holistic brief (Intent, prior decisions,
open risks, Intent-alignment check) instead of reading `~/.claude/sdd-memory/` files directly.
If it flags an Intent-alignment concern, surface it to the user before proceeding — don't
silently continue past a stated drift. If unavailable, skip this step entirely — surface one
plain notice and continue the workflow without a memory brief; this is never a blocking
condition.

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
reusable agent-nelly brief. `workflow-manager`'s own `start`-time Goal-seeding call and
`before-continue`'s Intent-alignment call are distinct-purpose, always-fresh calls outside this
dedup pool — see its Goal Field Contract section.

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
- `ux-agent` — delegate at every phase transition for the breadcrumb, chapter markers, and any
  spec-canvas Artifact. It does not own the `TaskCreate` checklist — see "Task Tracker Sync"
  below.

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
4. Do not resume, monitor, or drive `agent-TDD` past this initial spawn — anything after its
   own Green→Refactor review pause is outside this skill's scope.
5. If `agent-tdd` (or `agent-nelly` for the Pre-Slice Brief) is not installed, pause with a
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

## Auto-Advance Rules

After producing a phase artifact, auto-advance by default unless a flagged condition is
present: unresolved ambiguity, missing required fields, conflicting constraints, high-risk
migration, weak testability, a task too large for a safe TDD slice, or an
`agent-nelly:nelly-orchestrator` Intent-alignment flag not yet resolved with the user (only
applicable when it is available).

If a flagged condition exists: pause, explain the blocker clearly, do not advance until it's
resolved. When auto-advancing: update `workflow-state.md`, `recap.md`, the phase file's
`Status` section, and delegate to `ux-agent` to refresh the breadcrumb/checklist.

## Design Gate

Ready to advance into `Tasks` only when: it maps clearly to approved requirements, touched
modules/interfaces/boundaries are explicit (grounded in `planning-agent`'s findings, not
guessed), validation strategy is credible, tradeoffs and edge-case handling are documented, no
unresolved contradiction remains, and no unresolved Security Finding remains.

## Native Plan Mode

`workflow-manager` owns entering native plan mode (`EnterPlanMode`) at `before-design` and
exiting it (`ExitPlanMode`) at `after-tasks` once the `Tasks` checklist passes — see its "Native
Plan Mode Gate" section for the full contract. This stays here in the orchestrator rather than
`ux-agent` because it is a user-facing approval checkpoint (`ux-agent` never talks to the user).
Requesting approval this way is in addition to the phase gates above, not instead of them —
`ExitPlanMode` is only ever called once the Tasks checklist has already passed.

## TDD Slice Rule

A safe slice targets one behavior change and/or one file or module touched. If a task is too
large: propose a smaller slice, ask for confirmation, only then continue. This sizing discipline
is what makes the eventual `agent-tdd` handoff safe — `agent-tdd` enforces its own slice-sizing
too, but a well-sliced `tasks.md` avoids that friction entirely.

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

## Guardrails

- Do not require the user to manually prompt each phase skill.
- Do not move into `Design` until requirements pass the gate.
- Do not move into `Tasks` until design is coherent and testable.
- Do not allow oversized tasks to pass through unchanged.
- Do not drive the Red-Green-Refactor loop or the code-review gate — those belong solely to
  `agent-tdd` and `code-reviewer` after the Implementation Handoff.
- Do not hide gaps with broad assumptions, and do not hide an Intent-alignment flag.
- Do not hand-roll breadcrumb/checklist rendering — delegate to `ux-agent`.
- Do not call `ExitPlanMode` before the `Tasks` checklist passes, and do not skip the plan-mode
  gate silently — fall back to conversational confirmation only when the tools are unavailable.
- Prefer interviewing the user over silently inventing product requirements.
