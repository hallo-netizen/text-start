from __future__ import annotations
import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import start

class StartDoorTests(unittest.TestCase):
    def test_pferdeatelier_positive(self):
        result = start.authorize("pferdeatelier")
        self.assertEqual(result["status"], "START_AUTHORIZED")
        self.assertEqual(result["target_repository"], "hallo-netizen/affiliate-pferdeportal")
        self.assertEqual(result["target_ref"], "konzept0-portal-neutral-20261002")
        self.assertEqual(result["target_workflow"], ".github/workflows/k0-authoring-context.yml")
        self.assertEqual(result["canonical_start_command"], "K0:start")
        self.assertEqual(result["article_content_authority"], "NONE")
        self.assertEqual(result["quality_rule_authority"], "NONE")

    def test_unknown_project_blocked(self):
        with self.assertRaisesRegex(start.Blocked, "PROJECT_NOT_ALLOWED"):
            start.authorize("unknown")

    def _tampered(self, key, value, expected=None):
        original = json.loads((start.PROJECTS / "pferdeatelier.json").read_text(encoding="utf-8"))
        tampered = copy.deepcopy(original)
        tampered[key] = value
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pferdeatelier.json").write_text(json.dumps(tampered), encoding="utf-8")
            with mock.patch.object(start, "PROJECTS", root):
                if expected:
                    with self.assertRaisesRegex(start.Blocked, expected):
                        start.authorize("pferdeatelier")
                else:
                    with self.assertRaises(start.Blocked):
                        start.authorize("pferdeatelier")

    def test_tampered_command_blocked(self):
        self._tampered("canonical_start_command", "python3 something_else.py", "PFERDEATELIER_COMMAND_DRIFT")

    def test_tampered_target_ref_blocked(self):
        self._tampered("target_ref", "main", "PFERDEATELIER_REF_DRIFT")

    def test_tampered_target_workflow_blocked(self):
        self._tampered("target_workflow", "anything.yml", "PFERDEATELIER_WORKFLOW_DRIFT")

    def test_old_concept_agent_route_blocked(self):
        self._tampered("canonical_start_command", "python3 concept_agent/intake_bridge.py prepare concept_agent/current/PSERC_METADATA_SNAPSHOT.json CONCEPT_AGENT_INTAKE.json", "PFERDEATELIER_COMMAND_DRIFT")

    def test_start_door_no_alternate_workflow_dispatch(self):
        door = (start.ROOT / ".github/workflows/text-start-door.yml").read_text(encoding="utf-8")
        self.assertIn("K0_ENTRY_VERIFIED", door)
        self.assertIn("ISSUE_AUTHOR_ASSOCIATION", door)
        self.assertIn("OWNER|MEMBER|COLLABORATOR", door)
        self.assertIn("if: github.event_name == 'issues' && github.event.action == 'opened'", door)
        self.assertIn("START_ISSUE_NUMBER:", door)
        self.assertIn("START_RUN_ID:", door)
        self.assertIn("'source_issue_number':int(issue_number)", door)
        self.assertIn("'source_run_id':int(run_id)", door)
        self.assertNotIn("workflow_dispatch:", door)
        self.assertNotIn('if [ "$EVENT_NAME" = "workflow_dispatch" ]', door)
        self.assertNotIn("/dispatches", door)
        self.assertNotIn("text-start-pferdeatelier.yml", door)
        self.assertNotIn("concept_agent/", door)

    def _run_actual_issue_entry(self, author: str, title: str, issue_number: str = "123") -> subprocess.CompletedProcess:
        """Run the actual checked-in Issue resolver with simulated GitHub event values."""
        door = (start.ROOT / ".github/workflows/text-start-door.yml").read_text(encoding="utf-8")
        section = door.split("      - name: Resolve request\n", 1)[1].split("      - name: Verify pinned K0 entry", 1)[0]
        script_lines = section.split("        run: |\n", 1)[1].splitlines()
        script = "\n".join(line[10:] for line in script_lines if line.startswith("          ")) + "\n"
        fixed = 'issue_number="${{ github.event.issue.number }}"'
        self.assertEqual(script.count(fixed), 1)
        script = script.replace(fixed, 'issue_number="' + issue_number + '"')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "projects").mkdir()
            (root / "projects/pferdeatelier.json").write_bytes((start.PROJECTS / "pferdeatelier.json").read_bytes())
            (root / "START_POLICY.json").write_bytes(start.POLICY.read_bytes())
            (root / "start.py").write_bytes((start.ROOT / "start.py").read_bytes())
            output = root / "github-output"
            env = dict(os.environ, ISSUE_TITLE=title, ISSUE_AUTHOR_ASSOCIATION=author, GITHUB_OUTPUT=str(output))
            result = subprocess.run(["bash", "-c", script], cwd=root, env=env, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                self.assertTrue((root / "START_AUTHORIZATION.json").exists())
                doc = json.loads((root / "START_AUTHORIZATION.json").read_text(encoding="utf-8"))
                self.assertEqual(doc["status"], "START_AUTHORIZED")
                self.assertIn("issue_number=" + issue_number, output.read_text(encoding="utf-8"))
            return result

    def test_issue_entry_positive_real_shell(self):
        proc = self._run_actual_issue_entry("OWNER", "START:pferdeatelier")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_issue_entry_rejects_untrusted_author_real_shell(self):
        for author in ("NONE", "FIRST_TIME_CONTRIBUTOR", "CONTRIBUTOR", ""):
            proc = self._run_actual_issue_entry(author, "START:pferdeatelier")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("START_AUTHOR_NOT_AUTHORIZED", proc.stdout + proc.stderr)

    def test_issue_entry_rejects_other_title_real_shell(self):
        for title in ("START:other", "K0:start", "START:pferdeatelier extra", ""):
            proc = self._run_actual_issue_entry("OWNER", title)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("START_TITLE_FORBIDDEN", proc.stdout + proc.stderr)

    def test_issue_entry_rejects_missing_issue_number(self):
        proc = self._run_actual_issue_entry("OWNER", "START:pferdeatelier", "")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("START_ISSUE_NUMBER_REQUIRED", proc.stdout + proc.stderr)

    def test_publish_or_quality_authority_blocked(self):
        for key, value in [
            ("publish_allowed", True),
            ("quality_rules_changed", True),
            ("article_content_rules_changed", True),
            ("production_logic_changed", True),
            ("free_parameters", True),
        ]:
            self._tampered(key, value)

if __name__ == "__main__":
    unittest.main()
