import importlib.util
import pathlib
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fm_agent_governance", ROOT / "scripts/fm_agent_governance.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class GovernanceTests(unittest.TestCase):
    def test_plan_and_dependency_gate(self):
        tasks, state, policy = mod.check()
        self.assertEqual(mod.eligible(tasks, state), ["LAB-01"])
        self.assertIn("AGENTS.md", policy["required_documents"])

    def test_success_needs_evidence(self):
        original = mod.read
        def fake(path):
            data = original(path)
            if path == mod.STATE:
                data["tasks"]["LAB-01"] = {"status": "VERIFIED", "evidence": {}}
            return data
        with patch.object(mod, "read", side_effect=fake):
            with self.assertRaises(mod.Denied):
                mod.check()

    def test_dependency_cycle(self):
        original = mod.read
        def fake(path):
            data = original(path)
            if path == mod.PLAN:
                data["tasks"][0]["depends_on"] = ["LAB-03"]
            return data
        with patch.object(mod, "read", side_effect=fake):
            with self.assertRaises(mod.Denied):
                mod.check()

    def test_secret_rejection(self):
        with self.assertRaises(mod.Denied):
            mod.safe("api_key=topsecretkeyvalue123")
        self.assertEqual(mod.safe("normal checkpoint"), "normal checkpoint")

    def test_no_agent_certification(self):
        args = type("Args", (), {"op": "checkpoint", "task": "LAB-01",
                                    "status": "VERIFIED", "actor": "claude", "summary": "done"})()
        with self.assertRaises(mod.Denied):
            mod.run(args)

    def test_wrong_branch_denied(self):
        args = type("Args", (), {"op": "preflight", "task": "LAB-01", "actor": "test"})()
        with patch.object(mod, "git", return_value="main"):
            with self.assertRaises(mod.Denied):
                mod.run(args)

if __name__ == "__main__":
    unittest.main()
