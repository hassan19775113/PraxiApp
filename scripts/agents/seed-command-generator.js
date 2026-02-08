#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const OUTPUT_DIR = process.env.AGENT_OUTPUT_DIR || 'agent-outputs';
const SEED_REPORT = path.join(OUTPUT_DIR, 'seed-orchestrator.json');
const SEED_SCRIPT_PATH = path.join('scripts', 'seeds', 'seed-auto.js');

function output(status, details = {}, exitCode = 0) {
  const payload = { status, ...details };
  console.log(JSON.stringify(payload, null, 2));
  process.exit(exitCode);
}

function readSeedReport() {
  if (!fs.existsSync(SEED_REPORT)) return null;
  try {
    return JSON.parse(fs.readFileSync(SEED_REPORT, 'utf8') || '{}');
  } catch (err) {
    return null;
  }
}

function resourcesNeedingSeed(report) {
  if (!report || !report.after) return [];
  return report.after.filter((r) => r.count === 0 || r.status >= 400 || r.status === 0).map((r) => r.key);
}

function generateSeedScript(resources) {
  const dir = path.dirname(SEED_SCRIPT_PATH);
  fs.mkdirSync(dir, { recursive: true });

  const script = `#!/usr/bin/env node\n\nimport { request } from 'playwright';\n\nconst BASE_URL = process.env.BASE_URL || 'http://localhost:8000';\nconst E2E_USER = process.env.E2E_USER || 'e2e_ci';\nconst E2E_PASSWORD = process.env.E2E_PASSWORD || 'e2e_ci_pw';\n\nasync function login() {\n  const api = await request.newContext({ baseURL: BASE_URL });\n  let res = await api.post('/api/auth/login/', { data: { username: E2E_USER, password: E2E_PASSWORD } });\n  if (!res.ok()) {\n    res = await api.post('/api/auth/login/', { data: { email: E2E_USER, password: E2E_PASSWORD } });\n  }\n  if (!res.ok()) {\n    throw new Error('Login failed: ' + res.status());\n  }\n  return api;\n}\n\nasync function seed() {\n  const api = await login();\n  const created = {};\n\n  async function post(path, data) {\n    const res = await api.post(path, { data });\n    if (!res.ok()) throw new Error('POST ' + path + ' failed: ' + res.status());\n    return await res.json();\n  }\n\n  // Patients\n  created.patient = await post('/api/patients/', { first_name: 'E2E', last_name: 'Patient', email: 'e2e.patient@example.com' });\n\n  // Appointments (payload may need adjustment to your schema)\n  created.appointment = await post('/api/appointments/', {\n    title: 'E2E Appointment',\n    patient: created.patient?.id,\n    start: new Date().toISOString(),\n    end: new Date(Date.now() + 30 * 60 * 1000).toISOString(),\n  });\n\n  // KPIs (placeholder payload)\n  created.kpi = await post('/api/kpis/', { name: 'E2E KPI', value: 1 });\n\n  // Operations (placeholder payload)\n  created.operation = await post('/api/operations/', { name: 'E2E Operation', status: 'scheduled' });\n\n  await api.dispose();\n  console.log(JSON.stringify({ status: 'ok', created }, null, 2));\n}\n\nseed().catch((err) => {\n  console.error(JSON.stringify({ status: 'error', message: err.message }, null, 2));\n  process.exit(1);\n});\n`;

  fs.writeFileSync(SEED_SCRIPT_PATH, script, 'utf8');
}

function main() {
  const report = readSeedReport();
  const missing = resourcesNeedingSeed(report);

  if (!missing.length) {
    output('skipped', { reason: 'no-missing-resources' });
  }

  generateSeedScript(missing);
  output('generated', { script: SEED_SCRIPT_PATH, resourcesSeeded: missing });
}

main();