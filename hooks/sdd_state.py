"""Shared helpers for SDD hooks: locate and parse the active workflow-state.md.

Kept dependency-free (stdlib only) so it runs under any python3.

Note: workflow-state.md lives under the central memory dir (see sdd_memory.memory_dir),
not under <root>/spec/*/. A legacy repo-local spec/ directory from before this convention
change is not migrated or supported by find_state_files/active_state_file -- none exist in
this canonical repo.
"""
import glob
import os
import re

from sdd_memory import memory_dir


def find_state_files(root):
    """Return workflow-state.md paths under <memory_dir(root)>/spec/*/ sorted newest-first."""
    pattern = os.path.join(memory_dir(root), "spec", "*", "workflow-state.md")
    files = glob.glob(pattern)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files


def active_state_file(root):
    """Most recently modified workflow-state.md under memory_dir(root), or None."""
    files = find_state_files(root)
    return files[0] if files else None


def parse_state(path):
    """Parse the `- Field: value` lines of a workflow-state.md into a dict.

    Keys are lowercased field names, e.g. 'current phase', 'implementation requested'.
    """
    fields = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return fields
    for line in text.splitlines():
        m = re.match(r"\s*[-*]\s*([A-Za-z][A-Za-z /]+?):\s*(.*\S)?\s*$", line)
        if m:
            key = m.group(1).strip().lower()
            val = (m.group(2) or "").strip()
            if key not in fields:
                fields[key] = val
    return fields


def is_pre_implementation(fields):
    """True when the workflow has NOT yet been approved for implementation."""
    impl = fields.get("implementation requested", "").strip().lower()
    status = fields.get("workflow status", "").strip().lower()
    if impl in ("yes", "y", "true"):
        return False
    if "complete" in status or "implement" in status and "await" not in status:
        # e.g. "Implementing" or "Complete" -> gate is open
        return False
    return True
