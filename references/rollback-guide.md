# Rollback Guide: Returning a Finding to agent-isdd

When `agent-tdd` or `code-reviewer` discovers that the *task itself* was wrong — not just
the implementation — it can request a rollback to an earlier spec phase. There are two paths
depending on whether agent-isdd is present in the same session.

## Automatic path (agent-isdd in the same session)

When you spawned `agent-tdd:agent-TDD` from an agent-isdd session and the `SubagentStop`
event fires in that same session, the hook handles everything automatically:

1. `hooks/subagent_report.py` sees the marker in the returned report and writes
   `rollback_pending` to `workflow-state.json`.
2. The next time you re-enter agent-isdd (e.g. `/isdd` or `/isdd-continue`),
   `workflow-manager`'s `before-continue` hook detects `rollback_pending` first and routes
   into the Rewind Contract at the target phase.

**You don't need to do anything.** Just re-enter agent-isdd after the agent-tdd session ends.

## Human-relay path (agent-isdd NOT in the same session)

This applies when:
- You resumed `agent-tdd` via `SendMessage` in a separate session, or
- `code-reviewer` ran in a session that doesn't include agent-isdd.

In this case there is no automatic hook. To relay the rollback:

1. **Find the marker** in the final report from `agent-tdd` or `code-reviewer`. It looks like:

   ```
   <!--SDD-ROLLBACK-REQUEST: target=<Requirements|Design|Tasks> reason="..."-->
   ```

2. **Open (or re-enter) your agent-isdd session** for this feature.

3. **Paste the marker line** into your message to agent-isdd. For example:

   ```
   <!--SDD-ROLLBACK-REQUEST: target=Design reason="The assumed interface in design.md section 3 doesn't exist — the module was renamed last sprint."-->
   ```

   `workflow-manager`'s `before-continue` hook recognises the marker in user input and
   routes into the Rewind Contract exactly as if it had arrived automatically.

4. agent-isdd will rewind to the named target phase and log the rollback in `recap.md`
   distinctly from a routine rewind.

## Which target phase to name

If the report's `target=` value is unclear or absent, default to the more conservative
(earlier) phase — it is always safe to re-confirm a phase that may have been correct rather
than to skip past one that actually needs revision.

| Finding | Target phase |
|---|---|
| Requirements missed a constraint or edge case | `Requirements` |
| Design assumed a wrong interface or architecture | `Design` |
| Task slicing was oversized or wrongly scoped | `Tasks` |
| Ambiguous — could be Design or Tasks | `Design` (more conservative) |
