"""Controlled entrypoint for scheduled OFFLINE/online normative portal observation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from kordena_fiscal.compliance.normative_watch import (
    NormativeWatchError,
    poll_normative_sources,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="NFCore read-only normative portal watch")
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--acknowledge-network", action="store_true")
    options = parser.parse_args()
    if (
        not options.acknowledge_network
        or os.environ.get("NFCORE_NORMATIVE_WATCH_ENABLED") != "true"
    ):
        parser.error("official-source polling requires explicit network flag and opt-in")
    try:
        events = poll_normative_sources(state_path=options.state_file)
    except NormativeWatchError:
        print(json.dumps({"status": "NO_GO", "reason": "normative observation unavailable"}))
        return 2
    print(
        json.dumps(
            {
                "status": "REVIEW_REQUIRED",
                "changes": [event for event in events if event["status"] != "UNCHANGED"],
                "sources_checked": len(events),
                "normative_approved": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
