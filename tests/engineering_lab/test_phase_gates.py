import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("fm_phase_gates", ROOT/"scripts/fm_phase_gates.py")
gates=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)

class PhaseTests(unittest.TestCase):
    def test_no_external_dependency_for_internal_tasks(self):
        with self.assertRaises(gates.PhaseDenied):
            gates.validate_phase_plan(dict.fromkeys(gates.STAGES, {}), [{"id":"T1","phase":"INTERNAL_BUILD","external_dependency":True}])
    def test_external_blocker_deferred(self):
        self.assertEqual(gates.classify_blocker({"category":"EXTERNAL"}, "INTERNAL_BUILD"), "DEFER_TO_EXTERNAL_PHASE")
    def test_internal_blocker_is_not_deferred(self):
        self.assertEqual(gates.classify_blocker({"category":"INTERNAL"}, "INTERNAL_BUILD"), "BLOCK_CURRENT_PHASE")
    def test_external_cannot_start_until_internal_certified(self):
        self.assertFalse(gates.can_enter("EXTERNAL_CONFIGURATION", {"completed":{"INTERNAL_BUILD":True}}))
        self.assertTrue(gates.can_enter("EXTERNAL_CONFIGURATION", {"completed":{"INTERNAL_BUILD":True, "INTERNAL_CERTIFICATION":True}}))
    def test_commercial_requires_homologation_and_human(self):
        completed=dict.fromkeys(gates.STAGES[:-1], True)
        self.assertFalse(gates.can_enter("COMMERCIAL_RELEASE", {"completed":completed}))
        self.assertTrue(gates.can_enter("COMMERCIAL_RELEASE", {"completed":completed,"human_commercial_approval":True}))
    def test_parallel_internal_work_continues(self):
        tasks=[{"id":"A","phase":"INTERNAL_BUILD"},{"id":"B","phase":"INTERNAL_BUILD","depends_on":["A"]},{"id":"C","phase":"INTERNAL_BUILD"},{"id":"EXT","phase":"EXTERNAL_HOMOLOGATION","external_scope":"SEFAZ"}]
        self.assertEqual(gates.eligible_internal_tasks(tasks, {"A":"VERIFIED","B":"PENDING","C":"PENDING","EXT":"BLOCKED_EXTERNAL"}),["B","C"])
    def test_cannot_label_mock_as_external_gate(self):
        self.assertFalse(gates.can_enter("EXTERNAL_HOMOLOGATION", {"completed":{"INTERNAL_BUILD":True,"INTERNAL_CERTIFICATION":True}}))

if __name__=="__main__": unittest.main()
