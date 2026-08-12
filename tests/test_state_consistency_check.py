"""Tests for hooks/state_consistency_check.py.

New PostToolUse hook (2026-08-12, ISDD Sibling-Plugin Hook Reliability feature, Phase 2):
verify+repair workflow-state.json toward workflow-state.md on every write to the .md file,
never blocking. Follows subagent_report.py's pattern of writing directly to recap/ rather
than only reminding the model, and phase_task_sync.py's file-path matcher pattern.
"""
import json
import os
import unittest

import hook_test_utils as h


class StateConsistencyCheckTests(unittest.TestCase):
    def _seed(self, home, repo, md_fields, json_fields):
        feature_dir = h.feature_spec_dir(home, repo)
        md_path = h.seed_state_file(feature_dir, **md_fields)
        json_path = os.path.join(feature_dir, "workflow-state.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(json_fields, fh)
        return feature_dir, md_path, json_path

    def test_non_workflow_state_write_is_noop(self):
        with h.temp_git_repo() as repo, h.temp_home() as home:
            msg, rc = h.run_hook_message(
                "state_consistency_check.py",
                {"tool_input": {"file_path": "/some/other/file.md"}, "cwd": repo},
                env_extra={"HOME": home},
            )
            self.assertEqual(rc, 0)
            self.assertIsNone(msg)

    def test_consistent_state_is_noop(self):
        with h.temp_git_repo() as repo, h.temp_home() as home:
            feature_dir, md_path, json_path = self._seed(
                home, repo,
                {"current_phase": "Tasks", "workflow_status": "In Progress"},
                {"current_phase": "Tasks", "phase_state": "In Progress"},
            )
            with open(json_path) as fh:
                before = fh.read()
            msg, rc = h.run_hook_message(
                "state_consistency_check.py",
                {"tool_input": {"file_path": md_path}, "cwd": repo},
                env_extra={"HOME": home},
            )
            self.assertEqual(rc, 0)
            self.assertIsNone(msg)
            with open(json_path) as fh:
                self.assertEqual(fh.read(), before)

    def test_drift_is_repaired_toward_md_and_logged(self):
        with h.temp_git_repo() as repo, h.temp_home() as home:
            feature_dir, md_path, json_path = self._seed(
                home, repo,
                {"current_phase": "Design", "workflow_status": "In Progress"},
                {"current_phase": "Tasks", "phase_state": "In Progress"},
            )
            msg, rc = h.run_hook_message(
                "state_consistency_check.py",
                {"tool_input": {"file_path": md_path}, "cwd": repo},
                env_extra={"HOME": home},
            )
            self.assertEqual(rc, 0)
            self.assertIsNotNone(msg)

            with open(json_path) as fh:
                repaired = json.load(fh)
            self.assertEqual(repaired["current_phase"], "Design")
            self.assertIn("hook_history", repaired)
            self.assertEqual(repaired["hook_history"][-1]["hook"], "state_consistency_check")

            recap_path = os.path.join(feature_dir, "recap", "recap.md")
            with open(recap_path) as fh:
                recap_text = fh.read()
            self.assertIn("state_consistency_check", recap_text)
            self.assertIn("current_phase", recap_text)

    def test_missing_json_sibling_is_noop_no_crash(self):
        with h.temp_git_repo() as repo, h.temp_home() as home:
            feature_dir = h.feature_spec_dir(home, repo)
            md_path = h.seed_state_file(feature_dir, current_phase="Design")
            msg, rc = h.run_hook_message(
                "state_consistency_check.py",
                {"tool_input": {"file_path": md_path}, "cwd": repo},
                env_extra={"HOME": home},
            )
            self.assertEqual(rc, 0)
            self.assertIsNone(msg)

    def test_missing_md_file_is_noop_no_crash(self):
        with h.temp_git_repo() as repo, h.temp_home() as home:
            msg, rc = h.run_hook_message(
                "state_consistency_check.py",
                {"tool_input": {"file_path": os.path.join(home, "workflow-state.md")}, "cwd": repo},
                env_extra={"HOME": home},
            )
            self.assertEqual(rc, 0)
            self.assertIsNone(msg)


if __name__ == "__main__":
    unittest.main()
