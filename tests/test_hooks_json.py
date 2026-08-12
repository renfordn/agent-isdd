"""Structural tests for hooks/hooks.json -- confirms new hook registrations exist and the
file stays valid JSON, without needing to actually fire each hook (see the corresponding
test_<hook_name>.py files for behavioral coverage).
"""
import json
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_JSON = os.path.join(REPO_ROOT, "hooks", "hooks.json")


def _load():
    with open(HOOKS_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _commands_for(config, event, matcher_substr=None):
    commands = []
    for entry in config.get("hooks", {}).get(event, []):
        if matcher_substr and matcher_substr not in entry.get("matcher", ""):
            continue
        for h in entry.get("hooks", []):
            commands.append(h.get("command", ""))
    return commands


class HooksJsonStructureTests(unittest.TestCase):
    def test_is_valid_json(self):
        _load()  # raises on malformed JSON

    def test_state_consistency_check_registered_on_post_tool_use(self):
        config = _load()
        commands = _commands_for(config, "PostToolUse", "Edit|Write|MultiEdit|NotebookEdit")
        self.assertTrue(any("state_consistency_check.py" in c for c in commands))
        self.assertTrue(any("phase_task_sync.py" in c for c in commands))

    def test_slice_spec_gate_registered_on_pre_tool_use_task(self):
        config = _load()
        commands = _commands_for(config, "PreToolUse", "Task")
        self.assertTrue(any("slice_spec_gate.py" in c for c in commands))


if __name__ == "__main__":
    unittest.main()
