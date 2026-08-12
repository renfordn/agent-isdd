#!/usr/bin/env python3
"""PostToolUse hook: verify and repair workflow-state.json against workflow-state.md
whenever workflow-state.md is written.

workflow-state.md is always authoritative (see workflow-manager's Conflict Resolution
Rules); this hook performs the mechanical repair itself rather than merely reminding the
model to do it, the same way subagent_report.py already writes to recap/ directly instead
of only nudging. Repair is scoped to the small set of fields workflow-state.json actually
mirrors from workflow-state.md (see references/workflow-state.template.json) -- it never
invents values for JSON-only fields (hook_history, blocked_fields, recap_path, ...).

Never blocks: this is drift repair, not a gate. Compare hooks/commit_audit_gate.py, the one
hook in this plugin that does hard-deny -- deliberately narrower in scope (a single
`git commit` call) than every workflow-state.md write would be.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdd_state import parse_state, parse_state_json, write_state_json  # noqa: E402

FIELD_MAP = {
    "current phase": "current_phase",
    "workflow status": "phase_state",
    "pause reason": "pause_reason",
    "implementation requested": "implementation_requested",
}


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    norm = file_path.replace("\\", "/")
    if not norm.endswith("workflow-state.md"):
        sys.exit(0)

    if not file_path or not os.path.isfile(file_path):
        sys.exit(0)

    json_path = os.path.join(os.path.dirname(file_path), "workflow-state.json")
    if not os.path.isfile(json_path):
        sys.exit(0)  # no paired .json to repair -- not this hook's job to fabricate one

    md_fields = parse_state(file_path)
    json_fields = parse_state_json(json_path)

    repairs = {}
    for md_key, json_key in FIELD_MAP.items():
        md_val = md_fields.get(md_key)
        if md_val is None:
            continue
        if json_fields.get(json_key) != md_val:
            repairs[json_key] = md_val

    if not repairs:
        sys.exit(0)

    for json_key, md_val in repairs.items():
        json_fields[json_key] = md_val

    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    json_fields["last_updated"] = ts
    history = json_fields.setdefault("hook_history", [])
    history.append({
        "hook": "state_consistency_check",
        "outcome": "Repaired State",
        "decision": "continue",
        "timestamp": ts,
    })
    write_state_json(json_path, json_fields)

    field_list = ", ".join(sorted(repairs.keys()))
    feature_dir = os.path.dirname(file_path)
    recap_path = os.path.join(feature_dir, "recap", "recap.md")
    note = (
        f"\n- {ts}: state_consistency_check repaired workflow-state.json toward "
        f"workflow-state.md ({field_list}).\n"
    )
    try:
        os.makedirs(os.path.dirname(recap_path), exist_ok=True)
        with open(recap_path, "a", encoding="utf-8") as fh:
            fh.write(note)
    except OSError:
        pass

    print(json.dumps({"systemMessage": (
        f"SDD: repaired workflow-state.json drift ({field_list}) toward "
        f"workflow-state.md and logged it in recap.md."
    )}))
    sys.exit(0)


if __name__ == "__main__":
    main()
