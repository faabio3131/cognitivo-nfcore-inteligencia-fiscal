# FM Engineering Supervisor v0.1 — NFCore EGM laboratory

A **deterministic safeguard**, not another `AGENTS.md` prompt. This lab does **not** modify fiscal code, execute models, connect customer accounts, or perform a deployment.

## Purpose

- Keep the approved architecture's findings as persistent, task-addressable requirements.
- Refuse to recognize unproven `DONE` statuses, missing prerequisites, nonexistent files, tampered logs and stale commit evidence during final local checks.
- Expose the next eligible internal task without falsely marking external setup as a blocker to unrelated internal construction.
- Route lifecycle events to all **seven upstream EGM skill names**. Routing does not equal execution: `egm-review` and `egm-review-loop` require actual native isolated Goldfish subagents. Normal ChatGPT cannot certify them by following text instructions.
- Make automated checks independent of the executor's chat context. CI still needs to be configured as a required check through repository rules before it can prevent merges.

## Current NFCore seed

`plan.json` contains the **10 actions A01–A10 / 36 unique findings** extracted from the EGM `consolidated_review_report.md` exported 2026-11-10. They start OPEN. It does not claim that NFCore's cognitive architecture has passed review. The ZIP digest and reviewed SHA are recorded as provenance, while full subagent transcripts were **not independently exported**. Do not upgrade the execution verdict to full isolation certification.

The A-items are architectural findings, not the full NFCore task ledger. They **supplement** the existing official master plan and must never replace it.

## Commands

```bash
python -m unittest discover -s fm_supervisor/tests -v
python -m fm_supervisor.cli validate --mode workflow
python -m fm_supervisor.cli next
python -m fm_supervisor.cli route idea-started
python -m fm_supervisor.cli route implementation-changed
python -m fm_supervisor.cli route design-ready
python -m fm_supervisor.cli validate --mode certify --head <exact-40-hex-sha>
```

`workflow` rejects invalid/faked closures while allowing unfinished work. `certify` rejects any unfinished items and requires evidence tied to the exact HEAD. Even a passing local certification check is **only locally evidenced**: a true release requires remote CI validation, native reviewer evidence and explicit release approval.

## EGM lifecycle routing

| Event | Original skill name | Normal ChatGPT | Native Goldfish needed? |
| --- | --- | --- | --- |
| idea-started | egm-brainstorm | Assisted | No |
| requirements-approved | egm-draft | Assisted | No |
| structure-indexed | egm-bootstrap | Assisted | No |
| design-ready | egm-review | Preparation only | **Yes** |
| review-findings | egm-resolve | Evaluate findings | Native findings must already exist |
| pr-submitted | egm-review-loop | Preparation only | **Yes** |
| implementation-changed | egm-drift-report | Assisted with GitHub read access | No |
| module-complete | egm-drift-report + egm-review-loop | Mixed | **Yes for review-loop** |
| saas-internally-built | egm-drift-report + egm-review + egm-review-loop | Final review | **Yes** |

The review skills are intended chiefly for design/specification documents. Test, performance, security and production readiness gates remain separate from EGM.

## Evidence contract for DONE items

A task needs `code_files`, full 40-character `commit_sha`, at least one PASS test with exact matching commit, a log file under the repo with verified SHA-256, `review_reference`, and all prerequisites DONE. `--mode certify` also requires the recorded SHA to be the candidate HEAD. A result text copied into a log can still be fabricated, so a separate trusted CI attestation is required before **real** certification.

This project's workflow only validates the supervisor's own integrity and task claims. It does **not** claim to run NFCore's full functional suite.

## Safety

No automatic merge, no deployment, no secrets, no use of real financial or fiscal operations. External setup never excuses missing internal implementation. No new runtime/LLM service is deployed in v0.1.
