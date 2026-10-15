"""Internal, synthetic contract gates for the published Web runtime profile."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ci/check_nfv1_web_functional_profile.py"


def _run(
    tmp_path: Path, profile: dict[str, object], strict: bool = False
) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "runtime-profile.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), str(path)]
    if strict:
        cmd.append("--require-all-paths")
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def test_missing_core_fails_closed(tmp_path: Path) -> None:
    result = _run(tmp_path, {"human_identity_configured": True})
    assert result.returncode == 1
    assert "portal_executor_configured" in result.stdout


def test_operational_shell_is_not_mistaken_for_full_web_parity(tmp_path: Path) -> None:
    profile: dict[str, object] = {
        key: True
        for key in (
            "human_identity_configured",
            "portal_executor_configured",
            "bridge_security_configured",
            "bridge_executor_configured",
            "portal_fiscal_operation_executor_configured",
            "password_recovery_configured",
            "password_reset_delivery_configured",
            "commercial_fulfillment_configured",
            "commercial_provisioning_configured",
            "commercial_activation_configured",
        )
    }
    profile["fiscal_operation_handlers_configured"] = []
    ordinary = _run(tmp_path, profile)
    strict = _run(tmp_path, profile, strict=True)
    assert ordinary.returncode == 0
    assert strict.returncode == 1
    assert json.loads(strict.stdout)["paths_configured"]["fiscal_handlers"] is False
    assert json.loads(strict.stdout)["all_development_paths_ready"] is False


def test_runtime_profile_does_not_echo_unknown_sensitive_fields(tmp_path: Path) -> None:
    result = _run(tmp_path, {"private_token": "private-secret"})
    assert result.returncode == 1
    assert "private-secret" not in result.stdout
