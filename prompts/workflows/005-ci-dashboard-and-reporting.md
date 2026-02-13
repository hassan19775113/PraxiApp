PROMPT-ID: 005
VERSION: 1.0.0
TITLE: CI Dashboard and Reporting
DESCRIPTION: Generate a CI dashboard artifact from agent outputs and publish it reliably.

FULL PROMPT TEXT:

You are a senior CI systems engineer.

Add a job to the CI pipeline that aggregates agent outputs into a single HTML dashboard artifact.

Requirements:
- Input: artifacts from upstream jobs (auth-validator, seed-orchestrator, page-smoke, flaky-classifier, selector-auditor, fix-agent-supervisor)
- Output:
  - artifacts/dashboard/dashboard.html
  - badge.svg in both artifacts/ and artifacts/dashboard/
- Must be resilient:
  - artifact downloads should be best-effort (avoid noise failures if missing)
  - dashboard generation should not depend on optional agents succeeding

Publishing:
- Publish the dashboard to GitHub Pages if Pages is enabled.
- If Pages is not enabled or dashboard missing, skip publish without failing the workflow.

Output:
- Update workflow wiring and any scripts needed.
