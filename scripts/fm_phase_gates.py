"""FM phase gates: internal construction is independent of external homologation."""
from __future__ import annotations

INTERNAL = ("INTERNAL_BUILD", "INTERNAL_CERTIFICATION")
EXTERNAL = ("EXTERNAL_CONFIGURATION", "EXTERNAL_HOMOLOGATION")
STAGES = INTERNAL + EXTERNAL + ("COMMERCIAL_RELEASE",)

class PhaseDenied(ValueError):
    pass

def validate_phase_plan(phases: dict, tasks: list[dict]) -> None:
    if tuple(phases) != STAGES:
        raise PhaseDenied("Phase policy must define the canonical ordered stages")
    for task in tasks:
        if task.get("phase") not in STAGES:
            raise PhaseDenied(f"Unknown phase for {task.get('id')}")
        if task.get("external_dependency") and task["phase"] in INTERNAL:
            raise PhaseDenied("Internal task cannot require external credentials or homologation")
        if task.get("phase") in EXTERNAL and not task.get("external_scope"):
            raise PhaseDenied("External task requires explicit external_scope")
        if task.get("phase") == "COMMERCIAL_RELEASE" and not task.get("approval_required"):
            raise PhaseDenied("Commercial release requires explicit approval")

def can_enter(stage: str, evidence: dict) -> bool:
    if stage not in STAGES:
        raise PhaseDenied("Unknown phase")
    completed = evidence.get("completed", {})
    if stage == "INTERNAL_BUILD":
        return True
    if stage == "INTERNAL_CERTIFICATION":
        return completed.get("INTERNAL_BUILD") is True
    if stage == "EXTERNAL_CONFIGURATION":
        return (completed.get("INTERNAL_BUILD") is True and
                completed.get("INTERNAL_CERTIFICATION") is True)
    if stage == "EXTERNAL_HOMOLOGATION":
        return (can_enter("EXTERNAL_CONFIGURATION", evidence) and
                completed.get("EXTERNAL_CONFIGURATION") is True)
    return (can_enter("EXTERNAL_HOMOLOGATION", evidence) and
            completed.get("EXTERNAL_HOMOLOGATION") is True and
            evidence.get("human_commercial_approval") is True)

def classify_blocker(blocker: dict, stage: str) -> str:
    if stage not in STAGES:
        raise PhaseDenied("Unknown phase")
    category = blocker.get("category")
    if category not in {"INTERNAL", "EXTERNAL"}:
        raise PhaseDenied("Blocker category must be explicit")
    if category == "EXTERNAL" and stage in INTERNAL:
        return "DEFER_TO_EXTERNAL_PHASE"
    return "BLOCK_CURRENT_PHASE"

def eligible_internal_tasks(tasks: list[dict], states: dict) -> list[str]:
    """External blockers cannot pause unrelated internal DAG work."""
    result = []
    for task in tasks:
        if task["phase"] not in INTERNAL:
            continue
        if states.get(task["id"]) in {"VERIFIED", "BLOCKED_INTERNAL"}:
            continue
        if all(states.get(dep) == "VERIFIED" for dep in task.get("depends_on", [])):
            result.append(task["id"])
    return result
