#!/usr/bin/env python3
"""SubagentStop hook: capture a finished SDD subagent's final report into the
active feature's recap log, so the delegation loop is never lost.

Only logs when (a) an SDD workflow is active and (b) the subagent's final message
looks like a phase-worker report (spec-reviewer / tdd-planner) -- keeps unrelated
subagents, and the plugin's own mechanical helpers (planning-agent, ux-agent),
from adding recap noise. Implementation-phase reports (agent-TDD / test-author)
are out of scope for this plugin -- they belong to the separate agent-tdd plugin.
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdd_state import active_state_file  # noqa: E402

# Markers that identify a spec-reviewer / tdd-planner report.
SDD_MARKERS = re.compile(
    r"(?i)(verdict|acceptance criteria|\bEARS\b|tasks\.md|handoff|"
    r"rewritten|readiness|phase status|recommended phase status)"
)

# Explicit, plugin-controlled marker the two phase-worker subagents emit as
# the first line of their final report. Preferred over SDD_MARKERS because it
# can't be coincidentally triggered by unrelated natural-language text.
EXPLICIT_MARKER = re.compile(r"<!--SDD-REPORT:(tdd-planner|spec-reviewer)-->")


def is_sdd_report(text):
    return bool(EXPLICIT_MARKER.search(text) or SDD_MARKERS.search(text))


def extract_last_assistant_text(transcript_path):
    blocks = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(ev, dict):
                    continue
                msg = ev.get("message") if isinstance(ev.get("message"), dict) else None
                role = ev.get("type") or (msg.get("role") if msg else "")
                is_assistant = role == "assistant" or (msg and msg.get("role") == "assistant")
                if not is_assistant:
                    continue
                content = msg.get("content") if msg else ev.get("content")
                if isinstance(content, str):
                    blocks.append(content)
                elif isinstance(content, list):
                    parts = [c.get("text", "") for c in content
                             if isinstance(c, dict) and c.get("type") == "text"]
                    joined = "\n".join(p for p in parts if p)
                    if joined:
                        blocks.append(joined)
    except OSError:
        return ""
    return blocks[-1].strip() if blocks else ""


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()
    state = active_state_file(cwd)
    if not state:
        sys.exit(0)

    report = extract_last_assistant_text(payload.get("transcript_path", ""))
    if not report or not is_sdd_report(report):
        sys.exit(0)  # not an SDD phase-worker report — stay quiet

    feature_dir = os.path.dirname(state)
    log = os.path.join(feature_dir, "recap", "subagent-reports.md")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## Subagent report — {ts}\n\n{report}\n"
    try:
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except OSError:
        sys.exit(0)

    print(json.dumps({"systemMessage": (
        f"SDD: captured a subagent report to {os.path.relpath(log, cwd)} — "
        f"integrate it into recap.md and update workflow-state."
    )}))
    sys.exit(0)


if __name__ == "__main__":
    main()
