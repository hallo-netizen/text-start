from __future__ import annotations
import copy
import json
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
        self.assertEqual(result["target_ref"], "main")
        self.assertEqual(result["target_workflow"], "text-start-pferdeatelier.yml")
        self.assertEqual(result["target_start_contract"], "CURRENT_PROJECT_1_TO_N")
        self.assertEqual(result["current_assignment_resolution"], "TARGET_RECEIVER_AT_RUN_TIME")
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

    def test_tampered_current_assignment_contract_blocked(self):
        self._tampered("target_start_contract", "FIXED_BATCH", "PROJECT_BINDING_INVALID:target_start_contract")
        self._tampered("current_assignment_resolution", "STATIC", "PROJECT_BINDING_INVALID:current_assignment_resolution")

    def test_tampered_target_workflow_blocked(self):
        self._tampered("target_workflow", "anything.yml", "PFERDEATELIER_WORKFLOW_DRIFT")

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
