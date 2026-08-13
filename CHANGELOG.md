# Changelog

## 0.1.7

### Changed
- Extracted UX rendering (breadcrumb, spec-canvas Artifacts, chapter markers, review dashboards,
  out-of-scope task chips) to the new sibling plugin `agent-ux`. This repo's local
  `agents/ux-agent.md` and `references/ux-conventions.md` are removed; every calling skill
  (`spec-driven-development`, `workflow-manager`, `requirements-agent`, `design-author`) and
  runtime surface (`hooks/phase_task_sync.py`, `hooks/subagent_report.py`,
  `statusline/sdd_statusline.py`, `commands/isdd-status.md`, `commands/isdd-rewind.md`,
  `references/artifact-templates.md`) now delegates to `agent-ux:ux-agent` instead, constructing
  the UX Event Envelope (`caller`, `event_type`, `phase_state`, `delta`, `artifact_path`) defined
  in `agent-ux`'s own `INTEROP.md`.
- `INTEROP.md`: new "→ agent-ux (UX rendering)" section, mirroring the existing `agent-nelly`
  soft-dependency pattern — `agent-ux` is a soft dependency; unavailability surfaces one plain
  notice per session and never blocks the workflow. References `agent-ux`'s own
  unavailability/fallback contract by name rather than restating it, per this extraction's
  design mitigation against duplicated fallback logic across future callers (`agent-tdd`,
  `code-reviewer`).
- `tests/test_phase_task_sync.py`: updated the reminder-message assertion from `"ux-agent"` to
  `"agent-ux:ux-agent"` to match the migrated hook wording; full suite (90 tests) still passes.
- `skills/tdd-planner/SKILL.md` and `skills/doc-consistency-auditor/SKILL.md` were confirmed to
  need no changes — `tdd-planner` has no live `ux-agent` delegation to migrate, and
  `doc-consistency-auditor`'s two `ux-agent` mentions are illustrative prose (an example, and a
  description of `code-reviewer`'s own unrelated rule), not live delegation calls.
- Validated via a full manual trace/dry-run of a Requirements→Design→Tasks→handoff cycle against
  `agent-ux`'s `INTEROP.md` envelope contract and its recorded example envelopes — output shape
  (breadcrumb always first, one line per action taken) matches the pre-extraction baseline.
- Token-cost comparison against the pre-extraction in-process baseline (Phase 5 of the
  `agent-ux` plugin extraction plan): measured using a documented approximation (character
  count ÷ 4; no tokenizer available in this environment), comparing OLD total = pre-extraction
  `agent-isdd/agents/ux-agent.md` (4928 chars, the fixed per-call system-prompt cost) + a
  reconstructed old-style narrated delegation prompt per event, versus NEW total =
  `agent-ux/agents/ux-agent.md` + `agent-ux/INTEROP.md` combined (10455 + 10404 = 20859 chars,
  the new fixed per-cross-plugin-call cost) + the actual recorded example-envelope JSON payload
  per event. Result for all 3 representative events: **regression, not parity** —
  `phase_transition` ~1402 → ~5318 tokens (+279%), `section_checkpoint` ~1484 → ~5393 tokens
  (+263%), `review_threshold` ~1497 → ~5527 tokens (+269%). The regression is driven almost
  entirely by the new fixed cost (`ux-agent.md` roughly doubled in size for the per-event-type
  dispatch, and `INTEROP.md` adds ~10.4KB never paid before per call), not by the `delta`
  payload shapes themselves, which stayed small. Per the extraction plan's Phase 5 blocker
  clause, this is escalated back to a Design-level decision rather than trimmed here — see the
  `agent-ux-plugin-extraction` proposal's tasks.md Phase 5 for the open blocker.
- Follow-up refactor pass (`agent-ux` commit `6fbc9b5`): trimmed redundant restatement between
  `INTEROP.md` and `ux-agent.md` (contract-level detail now owned solely by `INTEROP.md`;
  `ux-agent.md` cross-references rather than duplicates) and converted the per-`event_type`
  delta-shape prose to a table. Combined fixed cost 20859 → 17800 chars (-14.7%). All 6
  `EXPECTED-OUTPUTS.md` scenarios re-verified unchanged — no behavior regression. Recomputed
  comparison: `phase_transition` ~1402 → ~4621 tokens (+229%), `section_checkpoint` ~1484 →
  ~4702 tokens (+217%), `review_threshold` ~1497 → ~4715 tokens (+215%). **Still regressed for
  all 3 events** — closed roughly a third of the original gap, but full parity (design's stated
  "equal or smaller" success criterion) was not reached and, per the assessment carried out
  during this trim, does not appear closeable through further prose compression alone: the
  two-file cross-plugin contract (frontmatter, tool list, per-event dispatch logic, a separately
  maintained `INTEROP.md`) has an irreducible fixed cost the old single self-contained file never
  had to pay. Remains an open blocker pending a Design-level decision (see tasks.md Phase 5).
- **Measurement correction**: the two comparisons above both counted `agent-ux/INTEROP.md`
  toward "the new fixed per-call cost." It isn't one — `ux-agent.md` is fully self-contained at
  runtime (every dispatch section restates its own exact `delta` key set; its `../INTEROP.md`
  citations are maintainer cross-references, never a `Read` instruction), and the caller's
  delegation prompt doesn't embed `INTEROP.md` either. Re-measured with fixed cost =
  `ux-agent.md` alone. Also removed `ux-agent.md`'s "Guardrails" section, self-labeled
  `(recap — see dispatch sections above for full rule text)` — literal in-file duplicate prose
  (8759 → 8193 chars, `agent-ux` commit `72e9af6`). Corrected comparison: OLD = 4928 chars +
  hand-written prose-narration prompt (matching the JSON payloads' information content) vs. NEW
  = 8193 chars + the real envelope JSON from `references/example-envelopes/`. Result:
  `phase_transition` ~1295 → ~2152 tokens (+66%), `section_checkpoint` ~1386 → ~2227 (+61%),
  `review_threshold` ~1424 → ~2361 (+66%) — a real regression, roughly a third of the previously
  reported +215–279%, attributable to `ux-agent.md`'s move from prose-narration to structured
  envelope dispatch rather than to the extraction itself. Still an open blocker pending a
  Design-level decision — see `workflow-state.md`'s "Measurement Correction" section for the
  full methodology.
- **Decision: accepted.** The ~61-66% regression is accepted as the cost of
  `ux-agent.md`'s move from prose narration to structured, validated envelope dispatch — a
  robustness gain (explicit field validation, misuse detection, per-event gating rules stated
  inline), not extraction overhead. The `agent-ux` plugin extraction stands; this closes the
  Phase 5 blocker without further trimming. Design's stated "equal or smaller" success criterion
  is formally not met, but is superseded by this explicit accept decision.

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
