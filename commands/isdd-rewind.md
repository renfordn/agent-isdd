---
description: Rewind the active SDD workflow to an earlier phase (Requirements | Design | Tasks)
argument-hint: "[Requirements | Design | Tasks]"
---

Rewind the active spec-driven-development workflow to the target phase named in the argument:
$ARGUMENTS

This command does not implement rewind logic itself. Delegate entirely to the
`workflow-manager` skill's **Rewind Contract** section (`skills/workflow-manager/SKILL.md`):

1. Resolve the active feature's `workflow-state.md`/`workflow-state.json` and confirm the
   requested target phase (`Requirements`, `Design`, or `Tasks`) is earlier than or equal to
   `Current Phase`.
2. Invoke the Rewind Contract to perform the state mutation. Do not re-derive how
   `Current Phase`, `Workflow Status`/`phase_state`, or `Pause Reason`/`pause_reason` are set —
   the contract owns those rules.
3. If the target phase is later than `Current Phase`, or does not exist, refuse the rewind and
   surface the contract's pause reason — do not guess or force it.

After the contract runs, delegate to `ux-agent` to refresh the breadcrumb and sync the
`TaskCreate`/`TaskUpdate` checklist directly (`ux-agent` cannot reach deferred tools), then report
back to the user:

- The from-phase and to-phase of the rewind.
- The resulting `Current Phase` and `Workflow Status`.
- Any later-phase `Status`/blocked fields that were preserved untouched, per the contract —
  never report them as cleared or reset.
- The `recap.md` and `hook_history` log entries the contract recorded.

If the contract refuses the rewind, present its concrete reason and next action instead of the
rewind result.
