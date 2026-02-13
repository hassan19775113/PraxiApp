PROMPT-ID: 002
VERSION: 1.0.0
TITLE: Stabilization Issues Import Orchestrator
DESCRIPTION: Create an idempotent GitHub Actions workflow to import stabilization issues and attach them to a GitHub Project.

FULL PROMPT TEXT:

You are a senior CI/CD automation engineer.

Goal: create a single GitHub Actions workflow that imports a stabilization backlog from JSON into GitHub Issues and adds them to a GitHub Project (Projects v2).

Requirements:
- Trigger: workflow_dispatch
- Permissions:
  contents: read
  issues: write
  projects: write
- Input source:
  - Load a JSON file at automation/issues.json
  - Each entry contains at least: title, body, labels[], epic (numeric id)
- Behavior:
  - Idempotent: must not create duplicates
  - Full error visibility: do not hide failures
  - Add debugging steps: list repo and automation folder

Project integration:
- Add each created/found issue to a GitHub Project (Projects v2) using GraphQL:
  - addProjectV2ItemById
- Link child issues to epics using a Parent field via GraphQL:
  - updateProjectV2ItemFieldValue

Configuration:
- Read the following env vars:
  - PROJECT_ID
  - PROJECT_NUMBER
  - PARENT_FIELD_ID

Output:
- Output only the workflow YAML.
- No explanations.
