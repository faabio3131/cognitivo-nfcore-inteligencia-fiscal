"""Additive shared anti-abuse window state for first-party trial intake.

Version 18. No destructive DDL; public trial remains opt-in and requires
operator-governed migration before staging/production runtime activation.
"""

PUBLIC_TRIAL_RATE_VERSION = 18
PUBLIC_TRIAL_RATE_NAME = "public_trial_rate_windows"
PUBLIC_TRIAL_RATE_SCHEMA = (
    """CREATE TABLE fm_public_trial_rate_windows (
        scope_key TEXT NOT NULL,
        window_start BIGINT NOT NULL,
        hits INTEGER NOT NULL CHECK (hits >= 1),
        PRIMARY KEY (scope_key, window_start)
    )""",
)
