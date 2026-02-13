PROMPT-ID: 007
VERSION: 1.0.0
TITLE: Self-Heal Pipeline (Safe, Non-Code)
DESCRIPTION: Implement a guarded self-heal pipeline with strict separation of context preparation, decision, and safe execution.

FULL PROMPT TEXT:

You are a senior reliability engineer.

Implement a self-heal pipeline that is safe-by-default and does not edit code.

Stages:
1) startup-fix-agent (context only)
- Collect CI artifacts/logs.
- Call Cloud-Agent to obtain Developer-Agent classification/plan.
- Persist structured context.json.

2) self-heal-supervisor (policy gate)
- Read context.json.
- Decide whether self-heal is allowed.
- Write decision.json with reason and classification.
- Output should_self_heal flag.

3) self-heal-runner (execute safe actions)
- Only run safe actions (e.g., reseed, auth refresh, rerun subset of tests).
- Upload a structured report and captured logs.

Constraints:
- Must be gated (manual runs only when E2E fails).
- Must keep main CI signal focused on tests.
- Must upload artifacts even on failure (best-effort).
