PROMPT-ID: 006
VERSION: 1.0.0
TITLE: GitHub Actions Workflow Hardening
DESCRIPTION: Reduce CI noise failures, tighten success semantics, and harden tunnel/publishing behavior.

FULL PROMPT TEXT:

You are a senior CI/CD engineer.

Harden the GitHub Actions workflows to be reliable and secure:

1) Reduce noise failures
- Make artifact downloads best-effort where missing artifacts should not fail the run.

2) Tighten success semantics
- Ensure public tunnel/publishing jobs run only on full success.
- Avoid ambiguous gating conditions.

3) Secure tunnel behavior
- If using cloudflared, pin the version and verify SHA-256.
- Only allow a public tunnel on explicit manual intent (workflow_dispatch input).

4) Clear run/job naming
- Make the Actions UI readable.

Constraints:
- Do not add extra UX.
- Keep changes minimal and focused.
