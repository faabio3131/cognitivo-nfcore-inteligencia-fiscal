#!/usr/bin/env python3
"""FM lab: deterministic task DAG, preflight, checkpoint, resume and audit."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
from fm_phase_gates import STAGES, validate_phase_plan
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "engineering_lab"
PLAN, STATE, POLICY = [LAB / x for x in ("missions.json", "state.json", "policy.json")]
JOURNAL = LAB / "events.jsonl"
STATES = {"PENDING", "IN_PROGRESS", "BLOCKED_INTERNAL", "BLOCKED_EXTERNAL",
          "IMPLEMENTED_UNVERIFIED", "VERIFIED"}

class Denied(Exception):
    pass

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if p.returncode:
        raise Denied("Cannot inspect git state")
    return p.stdout.strip()

def check():
    plan, state, policy = read(PLAN), read(STATE), read(POLICY)
    tasks = {t["id"]: t for t in plan["tasks"]}
    phases = read(LAB / "phases.json")["stages"]
    if tuple(phases) != STAGES:
        raise Denied("Invalid or reordered canonical phase policy")
    validate_phase_plan(phases, [{"id": t["id"], "phase": "INTERNAL_BUILD"} for t in plan["tasks"]])
    if len(tasks) != len(plan["tasks"]) or set(tasks) != set(state["tasks"]):
        raise Denied("Task ID mismatch or duplicate")
    visiting, seen = set(), set()
    def visit(key):
        if key in visiting:
            raise Denied("Dependency cycle")
        if key in seen:
            return
        visiting.add(key)
        for dep in tasks[key].get("depends_on", []):
            if dep not in tasks:
                raise Denied("Unknown dependency")
            visit(dep)
        visiting.remove(key)
        seen.add(key)
    for key in tasks:
        visit(key)
    for key, item in state["tasks"].items():
        if item["status"] not in STATES:
            raise Denied("Invalid state")
        if item["status"] == "VERIFIED":
            if not item.get("evidence", {}).get("commit"):
                raise Denied("Completion without evidence")
            if any(state["tasks"][d]["status"] != "VERIFIED" for d in tasks[key].get("depends_on", [])):
                raise Denied("Completion before prerequisites")
    for name in policy["required_documents"]:
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise Denied("Missing authority: " + name)
    return tasks, state, policy

def eligible(tasks, state):
    return [key for key, task in tasks.items()
            if state["tasks"][key]["status"] in ("PENDING", "IN_PROGRESS", "IMPLEMENTED_UNVERIFIED")
            and all(state["tasks"][dep]["status"] == "VERIFIED"
                    for dep in task.get("depends_on", []))]

def safe(text):
    if re.search(r"(?i)(-----BEGIN .*PRIVATE KEY-----|(?:password|api_key|secret|token)\s*[:=]\s*\S{8,})", text):
        raise Denied("Secret-like material cannot enter checkpoints")
    return text

def write_atomic(path, data):
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".fm-")
    try:
        with os.fdopen(fd, "w", encoding="utf8") as file:
            json.dump(data, file, indent=2, sort_keys=True, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def event(task, actor, data):
    payload = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "task": task, "actor": actor, "data": data}
    safe(json.dumps(payload))
    with JOURNAL.open("a", encoding="utf8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

def journal_count():
    if not JOURNAL.exists():
        return 0
    lines = JOURNAL.read_text(encoding="utf8").splitlines()
    for line in lines:
        data = json.loads(line)
        if not {"at", "task", "actor", "data"} <= set(data):
            raise Denied("Corrupt event journal")
    return len(lines)

def run(args):
    tasks, state, policy = check()
    allowed = eligible(tasks, state)
    if args.op == "audit":
        print(json.dumps({"valid": True, "eligible": allowed, "events": journal_count()}))
        return
    if args.op == "resume":
        print(json.dumps({"eligible": allowed, "tasks": state["tasks"], "events": journal_count(),
                          "git_head": git("rev-parse", "HEAD")}, indent=2))
        return
    key = args.task or (allowed[0] if allowed else None)
    if key not in allowed:
        raise Denied("Mission locked or complete; eligible=" + repr(allowed))
    if args.op == "preflight":
        branch = git("branch", "--show-current")
        if branch not in policy["allowed_branches"]:
            raise Denied("Branch not allowed: " + branch)
        contract = {"task": key, "actor": args.actor, "tenant": policy["engineering_tenant"],
                    "branch": branch, "head": git("rev-parse", "HEAD"),
                    "authorities": {name: sha(ROOT/name) for name in policy["required_documents"]},
                    "acceptance": tasks[key]["acceptance"], "prohibited": policy["prohibited_actions"]}
        print(json.dumps(contract, indent=2))
    elif args.op == "checkpoint":
        if args.status not in {"IN_PROGRESS", "BLOCKED_INTERNAL", "BLOCKED_EXTERNAL", "IMPLEMENTED_UNVERIFIED"}:
            raise Denied("Agent cannot self-certify or use unsupported state")
        if not args.summary or len(args.summary) > 2000:
            raise Denied("Checkpoint summary is required, max 2000 chars")
        safe(args.summary)
        item = state["tasks"][key]
        item.update(status=args.status, summary=args.summary, actor=args.actor,
                    head=git("rev-parse", "HEAD"))
        write_atomic(STATE, state)
        event(key, args.actor, {"status": args.status, "head": item["head"], "summary": args.summary})
        print("Checkpoint persisted; certification NOT implied")
    elif args.op == "verify":
        if state["tasks"][key]["status"] != "IMPLEMENTED_UNVERIFIED":
            raise Denied("Must first checkpoint IMPLEMENTED_UNVERIFIED")
        evidence = read(ROOT / args.evidence)
        if (evidence.get("task") != key or evidence.get("commit") != git("rev-parse", "HEAD")
                or evidence.get("policy_sha256") != sha(POLICY)
                or not evidence.get("tests") or not evidence.get("review")):
            raise Denied("Missing or stale evidence")
        print("LOCAL EVIDENCE STRUCTURE VALID; NOT VERIFIED: remote CI and runtime still require trusted validation")

def main():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers(dest="op", required=True)
    for name in ("audit", "resume", "preflight", "checkpoint", "verify"):
        p = sp.add_parser(name)
        if name in ("preflight", "checkpoint", "verify"):
            p.add_argument("--task")
        if name in ("preflight", "checkpoint"):
            p.add_argument("--actor", default="unknown")
        if name == "checkpoint":
            p.add_argument("--status", required=True)
            p.add_argument("--summary", required=True)
        if name == "verify":
            p.add_argument("--evidence", required=True)
    try:
        run(parser.parse_args())
        return 0
    except (Denied, ValueError, KeyError, OSError) as err:
        print("GOVERNANCE DENIED:", err, file=sys.stderr)
        return 2
if __name__ == "__main__":
    sys.exit(main())
