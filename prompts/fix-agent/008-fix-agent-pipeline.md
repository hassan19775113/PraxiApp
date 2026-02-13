PROMPT-ID: 008
VERSION: 1.0.0
TITLE: Fix-Agent Pipeline (Patch Artifacts, Guarded)
DESCRIPTION: Implement a Fix-Agent pipeline that produces PR-ready patch artifacts with guardrails and no automatic PR/push.

FULL PROMPT TEXT:

You are a senior automation engineer.

Implement a Fix-Agent pipeline that prepares code change artifacts without flipping the main CI signal:

1) Prepare input
- Gather CI artifacts (Playwright logs, backend logs, reports).
- Call Cloud-Agent to obtain Developer-Agent fix instructions.
- Write a stable fix-agent/input.json.

2) Apply-and-validate
- Apply small, scoped changes only.
- Enforce guardrails:
  - maximum files touched
  - maximum lines changed
  - allowed paths limited to tests and minimal config
- Emit patch artifacts:
  - fix-agent/patch-<run_id>.diff
  - fix-agent/metadata-<run_id>.json

Constraints:
- No direct push, no PR creation by default.
- Best-effort behavior: must not turn a failing CI run into a passing one by masking core failures.
