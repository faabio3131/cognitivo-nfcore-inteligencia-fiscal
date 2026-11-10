"""Deterministic project-plan verification; never executes an LLM or modifies a repo.

Important boundary: this utility validates evidence *structure/integrity*, not whether
logs are truthful or whether a remote CI passed. Those require independently
trusted CI attestations. It never labels a model-only statement as certified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

STATUS = frozenset({"OPEN", "IN_PROGRESS", "EXTERNAL_PENDING", "DONE"})
HEX40 = re.compile(r"[0-9a-f]{40}", flags=re.ASCII)
HEX64 = re.compile(r"[0-9a-f]{64}", flags=re.ASCII)
ID = re.compile(r"[A-Z][0-9]{2,}", flags=re.ASCII)
EVENTS: dict[str, tuple[str, ...]] = {
    "idea-started": ("egm-brainstorm",),
    "requirements-approved": ("egm-draft",),
    "structure-indexed": ("egm-bootstrap",),
    "design-ready": ("egm-review",),
    "review-findings": ("egm-resolve",),
    "pr-submitted": ("egm-review-loop",),
    "implementation-changed": ("egm-drift-report",),
    "module-complete": ("egm-drift-report", "egm-review-loop"),
    "saas-internally-built": ("egm-drift-report", "egm-review", "egm-review-loop"),
}
REQUIRES_NATIVE = frozenset({"egm-review", "egm-review-loop"})
ALL_SKILLS = frozenset({
    "egm-bootstrap", "egm-brainstorm", "egm-draft", "egm-review",
    "egm-review-loop", "egm-resolve", "egm-drift-report"
})
assert {skill for skills in EVENTS.values() for skill in skills} == ALL_SKILLS


def _json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("plan must be a JSON object")
    return raw


def _head() -> str | None:
    try:
        ret = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = ret.stdout.strip().lower()
        return sha if HEX40.fullmatch(sha) else None
    except (OSError, subprocess.CalledProcessError):
        return None


def _safe_path(root: Path, rel: str) -> Path | None:
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        return None
    full = (root / rel).resolve()
    if full == root.resolve() or root.resolve() not in full.parents:
        return None
    return full


def _check_evidence(task: dict[str, Any], root: Path, head: str | None, certify: bool) -> list[str]:
    ident = task["id"]
    ev = task.get("evidence")
    errors: list[str] = []
    if not isinstance(ev, dict):
        return [f"{ident}: evidence must be an object"]
    commit = ev.get("commit_sha")
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        errors.append(f"{ident}: DONE requires a 40-hex commit_sha")
    if certify and head is not None and commit != head:
        errors.append(f"{ident}: evidence commit must match certified HEAD {head}")
    files = ev.get("code_files")
    if not isinstance(files, list) or not files or any(not isinstance(p, str) for p in files):
        errors.append(f"{ident}: DONE requires nonempty code_files")
    else:
        for p in files:
            resolved = _safe_path(root, p)
            if resolved is None or not resolved.is_file():
                errors.append(f"{ident}: missing/unsafe code_file {p!r}")
    tests = ev.get("tests")
    if not isinstance(tests, list) or not tests:
        errors.append(f"{ident}: DONE requires at least one test receipt")
    else:
        for i, test in enumerate(tests):
            if not isinstance(test, dict):
                errors.append(f"{ident}: test {i} must be an object")
                continue
            if not test.get("name") or test.get("result") != "PASS":
                errors.append(f"{ident}: test {i} requires a name and PASS result")
            if test.get("commit_sha") != commit:
                errors.append(f"{ident}: test {i} commit differs from task evidence")
            path = _safe_path(root, test.get("log_path", ""))
            actual_hash = test.get("log_sha256", "")
            if not isinstance(actual_hash, str) or not HEX64.fullmatch(actual_hash):
                errors.append(f"{ident}: test {i} requires SHA-256 of its log")
            elif path is None or not path.is_file():
                errors.append(f"{ident}: test {i} log is missing or outside repo")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != actual_hash:
                errors.append(f"{ident}: test {i} log hash mismatch")
    if not isinstance(ev.get("review_reference"), str) or not ev["review_reference"].strip():
        errors.append(f"{ident}: DONE requires a review_reference")
    return errors


def verify(plan: dict[str, Any], *, root: Path, mode: str = "workflow", head: str | None = None) -> list[str]:
    """Validate verifiable plan invariants; empty list => structurally valid.

    Mode 'workflow' permits unfinished work but NEVER unproven DONE items.
    Mode 'certify' requires all items DONE and evidence for the exact HEAD.
    Neither mode independently certifies GitHub checks or native Goldfish agents.
    """
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not isinstance(plan.get("project"), str) or not plan["project"].strip():
        errors.append("project must be nonempty")
    if plan.get("policy") != "BUILD_INTERNAL_FIRST":
        errors.append("policy must be BUILD_INTERNAL_FIRST")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return errors + ["tasks must be a nonempty list"]
    ids: list[str] = []
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{i}] is not an object")
            continue
        ident = task.get("id")
        if not isinstance(ident, str) or not ID.fullmatch(ident):
            errors.append(f"tasks[{i}] has an invalid id")
            continue
        ids.append(ident)
    if len(ids) != len(set(ids)):
        errors.append("duplicate task ids")
    by_id = {task["id"]: task for task in tasks if isinstance(task, dict) and task.get("id") in ids}
    head = head if head is not None else _head()
    if mode == "certify" and head is None:
        errors.append("certify requires a known git HEAD or explicit --head")
    for ident, task in by_id.items():
        deps = task.get("depends_on")
        if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps):
            errors.append(f"{ident}: depends_on must be a list of ids")
            deps = []
        for d in deps:
            if d not in by_id:
                errors.append(f"{ident}: missing dependency {d}")
            if d == ident:
                errors.append(f"{ident}: self dependency")
        if len(deps) != len(set(deps)):
            errors.append(f"{ident}: duplicate dependencies")
        if not isinstance(task.get("acceptance"), list) or not task["acceptance"] or any(not isinstance(a,str) or not a.strip() for a in task["acceptance"]):
            errors.append(f"{ident}: acceptance criteria must be nonempty")
        status = task.get("status")
        if status not in STATUS:
            errors.append(f"{ident}: invalid status {status!r}")
            continue
        if status == "EXTERNAL_PENDING" and task.get("external_dependency") is not True:
            errors.append(f"{ident}: external pending is permitted only for actual external dependencies")
        if status == "DONE":
            for d in deps:
                if d in by_id and by_id[d].get("status") != "DONE":
                    errors.append(f"{ident}: dependency {d} not DONE")
            errors.extend(_check_evidence(task, root, head, certify=mode == "certify"))
        elif mode == "certify":
            errors.append(f"{ident}: {status} is not DONE")
    colors: dict[str, int] = {}
    def visit(ident: str) -> None:
        if colors.get(ident) == 1:
            errors.append(f"{ident}: dependency cycle")
            return
        if colors.get(ident) == 2:
            return
        colors[ident] = 1
        for dep in by_id[ident].get("depends_on", []):
            if dep in by_id and dep != ident:
                visit(dep)
        colors[ident] = 2
    for ident in by_id:
        visit(ident)
    source = plan.get("source")
    if isinstance(source, dict) and source.get("agents_reported") == 7:
        found = {finding for item in by_id.values() for finding in item.get("origin_findings", [])}
        expected = source.get("raw_findings_reported")
        if isinstance(expected, int) and len(found) != expected:
            errors.append(f"EGM findings coverage {len(found)} != {expected}")
        if not source.get("native_log_attested_only"):
            errors.append("EGM manifest must honestly indicate its native logs are not independently verified")
    return sorted(set(errors))


def next_tasks(plan: dict[str, Any]) -> list[dict[str, str]]:
    by_id = {task["id"]:task for task in plan.get("tasks", [])}
    output: list[dict[str, str]] = []
    for task in plan.get("tasks", []):
        if task.get("status") not in ("OPEN", "IN_PROGRESS"):
            continue
        deps = task.get("depends_on", [])
        if all(by_id.get(d, {}).get("status") == "DONE" for d in deps):
            output.append({"id":task["id"], "title":task["title"], "status":task["status"]})
    return output


def route(event: str, *, native_available: bool = False) -> dict[str, Any]:
    if event not in EVENTS:
        raise ValueError("unknown event")
    skills = EVENTS[event]
    return {
        "event": event,
        "steps": [
            {
                "skill": skill,
                "execution": "NATIVE_REQUIRED" if skill in REQUIRES_NATIVE and not native_available else "ELIGIBLE_TO_INVOKE",
                "native_goldfish_required": skill in REQUIRES_NATIVE,
                "status": "NOT_EXECUTED",
            } for skill in skills
        ],
        "note": "Routing is not execution. ChatGPT text review cannot substitute native Goldfish subagents.",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fm-supervisor", description=__doc__)
    p.add_argument("--plan", type=Path, default=Path("fm_supervisor/plan.json"))
    sub = p.add_subparsers(dest="action", required=True)
    v=sub.add_parser("validate", help="Fail closed on invalid or unsupported DONE statuses")
    v.add_argument("--mode", choices=("workflow", "certify"), default="workflow")
    v.add_argument("--head", default=None)
    sub.add_parser("next", help="List next eligible tasks without changing state")
    r=sub.add_parser("route", help="Map an event to the original EGM skills")
    r.add_argument("event", choices=tuple(EVENTS))
    r.add_argument("--native-available", action="store_true", help="ONLY if actual independent subagent runtime is available")
    args=p.parse_args(argv)
    try:
        plan=_json(args.plan)
        if args.action == "route":
            print(json.dumps(route(args.event, native_available=args.native_available),ensure_ascii=False,indent=2))
            return 0
        errors=verify(plan, root=Path.cwd(), mode=getattr(args, "mode", "workflow"), head=getattr(args, "head", None))
        if errors:
            print(json.dumps({"status":"FAIL", "errors":errors},ensure_ascii=False,indent=2))
            return 1
        if args.action == "next":
            print(json.dumps({"status":"VALID", "ready":next_tasks(plan)},ensure_ascii=False,indent=2))
        elif args.action == "validate":
            print(json.dumps({"status":"VALID" if args.mode == "workflow" else "LOCALLY_EVIDENCED_ONLY", "mode":args.mode, "tasks":len(plan["tasks"]), "certified_by_ci":False},ensure_ascii=False,indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status":"FAIL", "errors":[str(exc)]},ensure_ascii=False))
        return 2

if __name__=="__main__":
    sys.exit(main())
