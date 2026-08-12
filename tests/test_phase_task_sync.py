"""Tests for hooks/phase_task_sync.py.

New test design (no prior ad-hoc coverage this session) -- the simplest hook in the repo:
purely stateless, no filesystem I/O beyond stdin/stdout.
"""
import unittest

import hook_test_utils as h


class PhaseTaskSyncTests(unittest.TestCase):
    def test_workflow_state_md_triggers_reminder(self):
        msg, rc = h.run_hook_message(
            "phase_task_sync.py",
            {"tool_input": {"file_path": "/some/feature/workflow-state.md"}},
        )
        self.assertEqual(rc, 0)
        self.assertIsNotNone(msg)
        self.assertIn("ux-agent", msg)

    def test_tasks_tasks_md_triggers_reminder(self):
        msg, rc = h.run_hook_message(
            "phase_task_sync.py",
            {"tool_input": {"file_path": "/some/feature/tasks/tasks.md"}},
        )
        self.assertEqual(rc, 0)
        self.assertIsNotNone(msg)

    def test_non_matching_path_is_silent(self):
        msg, rc = h.run_hook_message(
            "phase_task_sync.py",
            {"tool_input": {"file_path": "/some/feature/requirements/requirements.md"}},
        )
        self.assertEqual(rc, 0)
        self.assertIsNone(msg)

    def test_backslash_path_still_matches(self):
        msg, rc = h.run_hook_message(
            "phase_task_sync.py",
            {"tool_input": {"file_path": "C:\\some\\feature\\workflow-state.md"}},
        )
        self.assertEqual(rc, 0)
        self.assertIsNotNone(msg)

    def test_missing_tool_input_is_silent(self):
        msg, rc = h.run_hook_message("phase_task_sync.py", {})
        self.assertEqual(rc, 0)
        self.assertIsNone(msg)

    def test_malformed_json_does_not_crash(self):
        import subprocess
        result = subprocess.run(
            ["python3", "hooks/phase_task_sync.py"],
            input="not json{{{",
            capture_output=True,
            text=True,
            cwd=h.REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    # Sanity check per design.md's discipline: prove the test would catch a broken hook,
    # not just a vacuously-true assertion.
    def test_sanity_a_path_using_the_watched_suffix_as_a_substring_not_suffix_does_not_match(self):
        # e.g. "workflow-state.md.bak" must NOT match -- endswith, not "contains".
        msg, rc = h.run_hook_message(
            "phase_task_sync.py",
            {"tool_input": {"file_path": "/some/feature/workflow-state.md.bak"}},
        )
        self.assertEqual(rc, 0)
        self.assertIsNone(msg)


if __name__ == "__main__":
    unittest.main()
