# Changelog

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
