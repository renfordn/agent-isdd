# Changelog

## 0.1.6

### Added
- Cross-cutting token-efficiency pass across the planning workflow (savings come from structure
  and reuse, not from cutting content — no `Phase Completion`/`Approval Checkpoint`/`Task
  Readiness Checklist` item shrank).
- `references/artifact-templates.md`: `requirements.md` template gains a fixed four-key
  `## Non-Functional Constraints` section (Throughput, Data Volume, Concurrency, Latency
  Budget; each accepts `N/A: <reason>`) plus its Approval Checkpoint line; `tasks.md` template
  gains a structured `### Depends On` (bare `task-id` list) field per phase, alongside and
  distinct from the existing narrative `### Prerequisites` (381→396 lines).
- `skills/requirements-agent/SKILL.md`: interview mode now elicits Non-Functional Constraints as
  one closed-set-friendly question; `Required Requirement Fields` lists the new field.
- `skills/tdd-planner/SKILL.md` / `agents/tdd-planner.md`: replaced the informal "dependency
  notes" mention with a pointer to the structured `Depends On` field.
- `INTEROP.md`: confirms `Depends On` is intentionally excluded from the `agent-tdd` Slice Spec
  field mapping (single-slice handoff; phase ordering already carries the sequencing signal).
- `skills/workflow-manager/SKILL.md`: new "Recap-and-Drop" rule — once a phase's completion
  checklist passes, subsequent same-session prompts reference `recap.md`'s summary by default
  instead of re-quoting the full prior-phase artifact body; the full artifact stays on disk and
  remains re-readable on demand. Cross-checked `spec-driven-development`/`design-author`/
  `tdd-planner` for callsites that needed updating — none did.
- `skills/spec-driven-development/SKILL.md`: the existing three-trigger brief-reuse convention
  (no prior content in context / a rewind or Mid-Phase Change Classification since / an
  Intent-alignment divergence flagged since) now also covers still-valid `planning-agent`/
  `spec-reviewer` findings within the same continuous stretch of phase work, not only the
  agent-nelly brief — same triggers, re-verified against the finding-cache scenario rather than
  loosened, per the correctness-risk mitigation in this pass's design. `design-author`/
  `tdd-planner` now check for a reusable cached finding before re-delegating to `planning-agent`,
  which is the single largest expected runtime saving in this pass (skips a full `planning-agent`
  re-invocation when Design already produced the needed finding).
- New `references/subagent-conventions.md`: documents "Excluded — and why" as the house
  convention for any subagent performing candidate-file triage, citing `agents/planning-agent.md`
  as the canonical, already-compliant example; `spec-reviewer`/`tdd-planner` noted as confirmed
  non-applicable today. `agents/planning-agent.md` gains a one-line pointer to it.
- `references/example-feature/2026-07-01-profile-state-schema-migration/`: worked-example
  refresh showing the new `Non-Functional Constraints` block (`requirements.md`, 85→97 lines)
  and a genuine `Depends On` chain across its three task phases (`tasks.md`, 143→155 lines).

## 0.1.5

### Fixed
- `skills/spec-driven-development/SKILL.md`: Design Gate summary now mirrors
  `design-author/SKILL.md`'s "no unresolved Security Finding remains" bullet, added in 0.1.4,
  which had drifted out of sync between the two files (code-review finding).

## 0.1.4

### Added
- Deeper agent-nelly integration into agent-isdd's planning subagents (`planning-agent`,
  `spec-reviewer`) and the calling skills that invoke them.
- `agents/planning-agent.md`: accepts caller-passed agent-nelly `file-relevance` hits before
  its wide-pass sweep and skips wide-pass grep/glob for candidate files with a fresh hit;
  produces a concise, agent-friendly write-back summary (file or judged file-group) for every
  file its deep pass actually reads; new "Nelly summaries to write (if any)" return bullet;
  `Guardrails`' Read-only line gained a one-clause carve-out clarifying it means filesystem
  writes, not the caller's own nelly write-back call.
- `agents/spec-reviewer.md`: first-ever agent-nelly integration — uses a caller-passed brief
  for the source material's touched area, mirroring `workflow-manager`'s Availability Check
  phrasing.
- `agents/tdd-planner.md`: one clarifying sentence — this feature doesn't alter its existing
  direct-read judgment call from 0.1.3.
- `skills/design-author/SKILL.md`: makes the pre-sweep nelly call and the follow-up write-back
  call on `planning-agent`'s behalf (subagents can't spawn subagents in this harness); new
  Design Gate bullet blocking on an unresolved Security Finding.
- `skills/requirements-agent/SKILL.md`: makes the pre-delegation nelly call on
  `spec-reviewer`'s behalf.
- `references/artifact-templates.md`: new `design.md` section "Improvement Opportunities &
  Blast Radius" (Blast Radius / Security Findings (blocking) / Refactor & Reduction
  Opportunities (non-blocking) / Best-Practice Notes (non-blocking)); `recap.md`'s Open Items
  gained `Security`/`Improvement` tags.

## 0.1.3

### Changed
- Token-efficiency pass on the agent-isdd ↔ agent-nelly integration and on agent-isdd's own
  spec artifacts.
- `skills/spec-driven-development/SKILL.md`: declared as the single fetch point for
  `agent-nelly:nelly-orchestrator`'s holistic brief per continuous stretch of phase work, with
  three explicit re-fetch triggers (no prior brief in context, a rewind/Mid-Phase Change
  Classification since, an Intent-alignment divergence flagged since).
- `skills/design-author/SKILL.md`: reuses the brief passed down by the caller instead of
  always re-fetching.
- `skills/workflow-manager/SKILL.md`: documents its `start`/`before-continue` nelly calls as
  distinct-purpose and explicitly outside the new dedup pool.
- `agents/tdd-planner.md`: documents why its direct `requirements.md`/`design.md` reads are
  not a nelly-routing violation.
- `INTEROP.md`: records the brief-reuse convention as the cross-plugin-visible contract.
- `references/artifact-templates.md`: removed two redundant `Phase Completion` re-check
  lines (`requirements.md`, `design.md`) and consolidated `recap.md`'s `Open Questions` /
  `Technical Debt` / `Risks` sections into one `Open Items` section (368→360 lines).

## 0.1.2

### Added
- Sibling-plugin hook reliability: hook points (state consistency, the implementation
  handoff, mid-implementation rollback requests) are now verified/enforced rather than only
  reminders to the model.
- `hooks/state_consistency_check.py`: `PostToolUse` hook that verifies and repairs
  `workflow-state.json` toward `workflow-state.md` on every write, logging the repair to
  `recap.md` and `hook_history`. Never blocks.
- `hooks/slice_spec_gate.py`: `PreToolUse` hard deny-gate on the Implementation Handoff —
  blocks spawning `agent-tdd:agent-TDD`/`agent-tdd:test-author` when the constructed Slice
  Spec is missing a required field per `INTEROP.md`'s mapping table.
- `hooks/subagent_report.py`: recognizes a new `<!--SDD-ROLLBACK-REQUEST:...-->` marker so
  `agent-tdd`'s review-pause report (or a human relaying `code-reviewer`'s findings) can
  signal that a task — not just its implementation — was wrong; recorded as
  `rollback_pending` in `workflow-state.json`.
- `workflow-manager`'s "Rollback Request Intake" (part of `before-continue`): routes a
  pending rollback into the existing Rewind Contract automatically, logged distinctly from a
  routine rewind, with loop prevention on repeated requests.
- `workflow-manager`'s "Mid-Phase Change Classification": one documented rule for whether a
  mid-Design/mid-Tasks user change should redo the current phase in place or trigger a real
  rewind.
- `INTEROP.md`: new "← agent-tdd / code-reviewer (rollback request)" section documenting the
  marker convention and its automatic-vs-human-relay scope.
- `references/workflow-state.template.json`: additive `rollback_pending` field.

## 0.1.1

### Infra
- First public push: repo created at `github.com/renfordn/agent-isdd`. No functional changes
  since 0.1.0.

## 0.1.0

### Added
- Initial release of `agent-isdd`, split out of the `sdd` plugin (v1.7.0) to own only the
  planning side of an intent spec-driven-development workflow: Requirements → Design →
  Tasks. Ported unchanged: `requirements-agent`, `design-author`, `tdd-planner`,
  `doc-consistency-auditor` skills; `planning-agent`, `spec-reviewer`, `tdd-planner`,
  `ux-agent` subagents; `sdd_memory.py`/`sdd_state.py`/`session_start.py`/`stop_check.py`/
  `precompact_snapshot.py`/`phase_task_sync.py`/`memory_permission.py`/`memory_slug_guard.py`/
  `subagent_report.py`/`commit_audit_gate.py`/`diff_fingerprint.py` hooks.
- Trimmed `spec-driven-development` and `workflow-manager` skills: removed Implementation-stage
  ownership (the old 6-stage `planning/red/green/review/refactor/commit_check` state machine)
  and the direct `agent-TDD`/`code-reviewer` dispatch, replaced with a single one-directional
  handoff to `agent-tdd:agent-TDD` (with `agent-tdd:test-author` first for `high-risk` slices)
  once the Tasks phase's Task Readiness Checklist passes and implementation is requested.
- Renamed all commands from `/sdd*` to `/isdd*`.
- `references/workflow-state.template.json` simplified: dropped `implementation_stage`,
  `diff_fingerprint`, `review_state_path` fields, since Implementation-stage tracking now lives
  entirely inside `agent-tdd`.

### Removed
- `agent-TDD`/`test-author` agents and the `agent-TDD` skill — implementation and TDD
  orchestration now live solely in the separate `agent-tdd` plugin.
- `code-reviewer` skill — the review gate now lives solely in the separate `code-reviewer`
  plugin, invoked directly by whichever caller drives implementation (no longer this plugin).
- `dispatch_gate.py`, `gate_check.py` hooks — these gated `agent-TDD` dispatch and pre-approval
  source edits respectively; `agent-isdd` never touches source files, only planning artifacts,
  and `agent-tdd` self-gates its own dispatch.
- `REVIEW-STATE.md.template`, `REVIEW-HISTORY.md.template` reference templates — owned by
  `code-reviewer` now.

`~/.claude/sdd-memory/<project-slug>/spec/` artifacts are unchanged in directory layout and
file format — no migration is required from `sdd`.
