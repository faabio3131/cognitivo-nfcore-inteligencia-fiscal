#!/usr/bin/env python3
"""Validate unmodified EGM upstream checkout and seven original skill entrypoints."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EGM = ROOT / "third_party" / "elephant-goldfish-model"
EXPECTED = "6d2af49f635515a472ce0dbba375c62b73dace26"
SKILLS = ("egm-bootstrap", "egm-brainstorm", "egm-draft", "egm-review",
          "egm-review-loop", "egm-resolve", "egm-drift-report")
PERSONAS = ("bootstrap_orchestrator", "codebase_details", "comprehension",
            "design_critic", "implementation_readiness", "inventive_catalyst",
            "structural", "style", "synthesizer", "zoom_out")

def main():
    assert EGM.is_dir(), "EGM checkout missing; initialize git submodules"
    sha = subprocess.check_output(["git", "-C", str(EGM), "rev-parse", "HEAD"], text=True).strip()
    assert sha == EXPECTED, f"EGM SHA changed: {sha}"
    manifest = json.loads((EGM / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "egm"
    for skill in SKILLS:
        body = (EGM / "skills" / skill / "SKILL.md").read_text()
        assert "disable-model-invocation: true" in body, skill
    for persona in PERSONAS:
        assert (EGM / "agents" / (persona + ".md")).is_file(), persona
        assert (EGM / ".claude-plugin" / "agents" / (persona + ".md")).is_file(), persona
    for file in ("docs/claude.md", "docs/codex.md", "LICENSE"):
        assert (EGM / file).is_file(), file
    print(json.dumps({"egm_sha": sha, "skills": list(SKILLS), "personas": len(PERSONAS),
                      "status": "PACKAGING_VERIFIED_NOT_NATIVE_EXECUTED"}, indent=2))

if __name__ == "__main__":
    main()
