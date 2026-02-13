PROMPT-ID: 003
VERSION: 1.0.0
TITLE: Developer-Agent Log Processor + Cloud-Agent Forwarder
DESCRIPTION: Implement a Developer-Agent that processes CI logs and a Cloud-Agent that forwards CI logs to the Developer-Agent with strict auth and validation.

FULL PROMPT TEXT:

You are a senior meta-systems engineer.

Implement two Vercel serverless endpoints in TypeScript:

1) Developer-Agent
- Endpoint: POST /process-logs
- Responsibilities:
  - Require Bearer auth via DEVELOPER_AGENT_TOKEN
  - Validate JSON payload (required fields include run_id, job_name, timestamp, branch, commit, status, playwright_log, backend_log)
  - Trim logs to safe maximum sizes
  - Store logs and analysis under logs/<run_id>/
  - Classify failures into stable categories
  - Produce structured JSON output containing:
    - classification
    - self_heal_plan
    - fix_agent_instructions
    - triggers

2) Cloud-Agent
- Endpoint: POST /api/ci/logs
- Responsibilities:
  - Require Bearer auth via AGENT_TOKEN
  - Validate payload and forward it to the Developer-Agent
  - Forward using DEVELOPER_AGENT_URL and DEVELOPER_AGENT_TOKEN
  - Return upstream JSON to CI as { status: 'received', upstream: <Developer-Agent response> }

Constraints:
- Must be safe-by-default (no side effects beyond writing logs).
- Must return stable structured JSON for CI parsing.
- Must handle missing/misconfigured secrets with clear error responses.

Output:
- Write the implementation code and any required routing configuration.
- No extra pages or UI work.
