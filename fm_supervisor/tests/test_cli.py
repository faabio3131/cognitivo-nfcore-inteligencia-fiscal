"""No network or model consumption. Test failures a plan guard must detect."""
from __future__ import annotations
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from fm_supervisor.cli import ALL_SKILLS, EVENTS, next_tasks, route, verify

BASE = {
    "schema_version":1, "project":"Test SaaS", "policy":"BUILD_INTERNAL_FIRST",
    "tasks":[{"id":"A01", "title":"Backend", "depends_on":[], "status":"OPEN", "external_dependency":False, "acceptance":["Backend built"],"evidence":{}},
             {"id":"A02", "title":"UI", "depends_on":["A01"], "status":"OPEN", "external_dependency":False,"acceptance":["UI tested"],"evidence":{}}]
}
SHA = "a"*40

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/"code.py").write_text("print('test')\n",encoding="utf8")
        (self.root/"proof.log").write_text("1 passed\n",encoding="utf8")
        self.plan=copy.deepcopy(BASE)
    def errors(self, mode="workflow", head=SHA):
        return verify(self.plan,root=self.root,mode=mode,head=head)
    def done(self, ident="A01"):
        task=next(t for t in self.plan["tasks"] if t["id"] == ident)
        task["status"]="DONE"
        task["evidence"]={"commit_sha":SHA,"code_files":["code.py"],"review_reference":"PR-42",
                          "tests":[{"name":"unit", "result":"PASS", "commit_sha":SHA, "log_path":"proof.log",
                                    "log_sha256":hashlib.sha256((self.root/"proof.log").read_bytes()).hexdigest()}]}
    def test_unfinished_tasks_permitted_in_workflow(self):
        self.assertEqual(self.errors(),[])
    def test_unfinished_tasks_cannot_certify(self):
        self.assertIn("A01: OPEN is not DONE",self.errors("certify"))
    def test_next_respects_dependency(self):
        self.assertEqual([x["id"] for x in next_tasks(self.plan)],["A01"])
        self.done()
        self.assertEqual([x["id"] for x in next_tasks(self.plan)],["A02"])
    def test_done_with_real_local_receipt_accepted_structurally(self):
        self.done()
        self.assertEqual(self.errors(),[])
    def test_fake_done_without_evidence_fails(self):
        self.plan["tasks"][0]["status"]="DONE"
        self.assertTrue(any("DONE requires" in msg for msg in self.errors()))
    def test_stale_commit_fails_certification(self):
        self.done()
        self.done("A02")
        self.assertTrue(any("must match certified HEAD" in msg for msg in self.errors("certify",head="b"*40)))
    def test_good_local_evidence_not_remote_ci_certification(self):
        self.done(); self.done("A02")
        self.assertEqual(self.errors("certify"),[])
    def test_hash_tamper_is_detected(self):
        self.done()
        (self.root/"proof.log").write_text("failed\n")
        self.assertTrue(any("hash mismatch" in msg for msg in self.errors()))
    def test_malicious_path_escape_fails(self):
        self.done()
        self.plan["tasks"][0]["evidence"]["code_files"]=["../secret.py"]
        self.assertTrue(any("unsafe" in msg for msg in self.errors()))
    def test_dependency_not_done_rejected(self):
        self.done("A02")
        self.assertTrue(any("dependency A01 not DONE" in msg for msg in self.errors()))
    def test_external_pending_only_for_external(self):
        self.plan["tasks"][0]["status"]="EXTERNAL_PENDING"
        self.assertTrue(any("only for actual external" in msg for msg in self.errors()))
    def test_external_wait_does_not_block_unrelated_internal_task(self):
        self.plan["tasks"][0]["status"]="EXTERNAL_PENDING";self.plan["tasks"][0]["external_dependency"]=True
        self.plan["tasks"][1]["depends_on"]=[]
        self.assertEqual([x["id"] for x in next_tasks(self.plan)],["A02"])
        self.assertEqual(self.errors(),[])
    def test_cycle_is_rejected(self):
        self.plan["tasks"][0]["depends_on"]=["A02"]
        self.assertTrue(any("dependency cycle" in msg for msg in self.errors()))
    def test_unknown_dependency_rejected(self):
        self.plan["tasks"][0]["depends_on"]=["A99"]
        self.assertTrue(any("missing dependency" in msg for msg in self.errors()))
    def test_duplicate_id_rejected(self):
        self.plan["tasks"][1]["id"]="A01"
        self.assertTrue(any("duplicate task ids" in msg for msg in self.errors()))
    def test_all_seven_original_skills_have_routing(self):
        self.assertEqual(set(sum((list(x) for x in EVENTS.values()),[])),ALL_SKILLS)
    def test_normal_chat_does_not_fake_native_review(self):
        decision=route("design-ready", native_available=False)
        self.assertEqual(decision["steps"][0]["execution"],"NATIVE_REQUIRED")
        self.assertEqual(decision["steps"][0]["status"],"NOT_EXECUTED")
    def test_event_routing_never_claims_execution(self):
        for event in EVENTS:
            for step in route(event,native_available=True)["steps"]:
                self.assertEqual(step["status"],"NOT_EXECUTED")
    def test_missing_findings_coverage_rejected(self):
        self.plan["source"]={"agents_reported":7, "raw_findings_reported":2, "native_log_attested_only":True}
        self.plan["tasks"][0]["origin_findings"]=["S5-ZO-01"]
        self.assertTrue(any("findings coverage" in msg for msg in self.errors()))
    def test_honest_native_log_limitation_required(self):
        self.plan["source"]={"agents_reported":7,"raw_findings_reported":0,"native_log_attested_only":False}
        self.assertTrue(any("native logs" in msg for msg in self.errors()))

if __name__=="__main__":unittest.main()
