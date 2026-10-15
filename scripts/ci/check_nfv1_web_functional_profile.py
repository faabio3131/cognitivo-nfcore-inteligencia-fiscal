"""NFCore V1 internal Web capability gate from the canonical /runtime/profile.

Non-destructive: reports incomplete development wiring, never invokes fiscal services.
No external homologation or customer data is needed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

BOOL_KEYS = (
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

OPTIONAL_PATHS = {
    "fiscal_handlers": "fiscal_operation_handlers_configured",
    "commercial_checkout": "commercial_checkout_processing_configured",
    "commercial_acquisition": "commercial_first_party_acquisition_configured",
    "trial": "commercial_trial_configured",
    "cakto_webhook": "cakto_webhook_configured",
    "command_webhook": "command_webhook_configured",
}

def assess(profile: Mapping[str, Any]) -> dict[str, object]:
    """Only canonical, bounded keys; never dump arbitrary runtime values."""
    missing_core = [key for key in BOOL_KEYS if profile.get(key) is not True]
    fiscal = profile.get(OPTIONAL_PATHS["fiscal_handlers"])
    paths = {
        name: (
            bool(fiscal)
            if name == "fiscal_handlers" and isinstance(fiscal, list)
            else profile.get(key) is True
        )
        for name, key in OPTIONAL_PATHS.items()
    }
    return {
        "core_ready": not missing_core,
        "core_missing": missing_core,
        "paths_configured": paths,
        "commercial_catalog_published": profile.get("pricing_catalog_published") is True,
        "commercial_release_available": (
            profile.get("commercial_release_status") not in (None, "unavailable")
        ),
        "all_development_paths_ready": not missing_core
        and all(paths.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path, help="JSON snapshot from canonical /runtime/profile")
    parser.add_argument("--require-all-paths", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.profile.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        parser.error("profile must be a JSON object")
    result = assess(payload)
    print(json.dumps(result, sort_keys=True))
    return int(
        not result["core_ready"]
        or (args.require_all_paths and not result["all_development_paths_ready"])
    )


if __name__ == "__main__":
    raise SystemExit(main())
