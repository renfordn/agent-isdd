# agent-isdd

An intent spec-driven development workflow for Claude Code and Claude Desktop, scoped to the
planning side of the loop: EARS-based **Requirements**, research-backed **Design**, and
TDD-sized **Tasks**. It hands off cleanly to separate sibling plugins for everything after
planning:

- **[agent-tdd](https://github.com/renfordn/agent-tdd)** — implementation, strict
  Red-Green-Refactor TDD execution.
- **[code-reviewer](https://github.com/renfordn/code-reviewer)** — the mandatory review gate,
  invoked by whichever caller drives implementation.
- **[agent-nelly](https://github.com/renfordn/agent-nelly)** — goal-aware memory, briefs, and
  cross-project promotion.

`agent-isdd` never drives the TDD loop, never invokes the review gate, and never owns a memory
subsystem beyond its own per-feature `spec/` artifacts. It produces a Slice Spec at the
Tasks → Implementation boundary and stops.

## Why this plugin exists

`agent-isdd` is the successor to the `sdd` plugin, which originally bundled requirements,
design, tasks, TDD implementation, code review, and memory into a single, oversized plugin.
Implementation, review, and memory were extracted first (`agent-tdd`, `code-reviewer`,
`agent-nelly`); this plugin is the last piece — the planning-only remainder of `sdd`, trimmed of
everything the siblings now own. See `CHANGELOG.md` for the full port/trim/drop breakdown.

## Workflow

Phase-gated, always in order: `Requirements` → `Design` → `Tasks`. Each phase has a hard
completion checklist (EARS format, no unresolved ambiguity, explicit interfaces/touchpoints,
safe TDD-sized slices) before the next phase opens. State lives in
`~/.claude/sdd-memory/<project-slug>/spec/<feature-slug>/`.

## Commands

- `/isdd` — start or continue the workflow for a feature.
- `/isdd-status` — show current phase, status, blockers, next action (read-only).
- `/isdd-continue` — force-continue from the current phase.
- `/isdd-rewind` — rewind to an earlier phase (Requirements | Design | Tasks).
- `/isdd-init` — first-run onboarding for a new project.
- `/isdd-memory` — view or migrate this project's central memory (redirects to `agent-nelly`).

## Handoff contract

At the end of Tasks, once the Task Readiness Checklist passes and implementation is requested,
`agent-isdd` builds a **Slice Spec** from `tasks.md`/`design.md` and spawns
`agent-tdd:agent-TDD` (or `agent-tdd:test-author` first, for `high-risk` slices). This is a
one-directional handoff — `agent-isdd` does not resume or drive `agent-TDD` past the initial
spawn. See `INTEROP.md` for the exact field mapping.
