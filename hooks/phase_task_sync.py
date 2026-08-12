#!/usr/bin/env python3
"""PostToolUse hook: remind the agent to sync the visible progress UI whenever
a phase or slice artifact changes.

Generalizes the old tasks.md-only reminder to every phase-transition surface
(workflow-state.md, tasks/tasks.md) now that the breadcrumb + TaskCreate/
TaskUpdate checklist convention (see references/ux-conventions.md) applies to
every phase and every TDD slice, not just the Tasks phase. Only the model can
call TaskCreate/TaskUpdate/Artifact, so this hook can't perform the sync
itself — it fires a reminder that the sync is owed. The breadcrumb is
ux-agent's job; the TaskCreate/TaskUpdate checklist is the calling skill's own
job (ux-agent's isolated subagent context can't reach deferred tools).
"""
import json
import os
import sys

WATCHED_SUFFIXES = ("workflow-state.md", "tasks/tasks.md")


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    norm = file_path.replace("\\", "/")
    if not any(norm.endswith(suffix) for suffix in WATCHED_SUFFIXES):
        sys.exit(0)

    print(json.dumps({
        "systemMessage": (
            "SDD: a phase/slice artifact was written. Delegate to the "
            "ux-agent subagent for the breadcrumb line, and sync the "
            "TaskCreate/TaskUpdate/TaskList checklist directly from the "
            "calling skill (ux-agent's subagent context can't reach those "
            "deferred tools) — see references/ux-conventions.md."
        )
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
