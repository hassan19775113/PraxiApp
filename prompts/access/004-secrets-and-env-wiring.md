PROMPT-ID: 004
VERSION: 1.0.0
TITLE: Agent Secrets and Environment Wiring
DESCRIPTION: Define and wire required environment variables/secrets for CI log shipping and Developer-Agent integration.

FULL PROMPT TEXT:

You are a senior DevOps/security engineer.

Define the minimal environment-variable contract for an agent-driven CI system where GitHub Actions ships logs to a Cloud-Agent, which forwards to a Developer-Agent.

Required:
- AGENT_TOKEN (Cloud-Agent inbound auth)
- DEVELOPER_AGENT_URL (Cloud-Agent forward base URL)
- DEVELOPER_AGENT_TOKEN (Cloud-Agent outbound auth to Developer-Agent)
- DEVELOPER_AGENT_TOKEN (Developer-Agent inbound auth)

Deliverables:
- Provide a template env file snippet (or update an existing env template) documenting the variables.
- Ensure the Cloud-Agent and Developer-Agent endpoints enforce the Bearer tokens.
- Ensure CI jobs that call the Cloud-Agent read AGENT_TOKEN from GitHub secrets.

Constraints:
- Do not print secrets.
- Use consistent naming.
- Prefer explicit validation and clear error messages.
