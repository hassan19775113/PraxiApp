#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const OUTPUT_DIR = process.env.AGENT_OUTPUT_DIR || 'agent-outputs';
const AUDITOR_REPORT = path.join(OUTPUT_DIR, 'selector-auditor.json');
const REPORT_PATH = path.join(OUTPUT_DIR, 'selector-refactor-report.json');

// Map auditor keys to page object files and replacement selectors
const REPLACEMENTS = {
  'calendar.anchor': {
    file: path.join('tests', 'pages', 'calendar-page.ts'),
    from: "page.locator('#appointmentCalendar')",
    to: "page.getByTestId('appointmentCalendar')",
  },
  'patients.anchor': {
    file: path.join('tests', 'pages', 'patients-page.ts'),
    from: "page.locator('#patientSelect')",
    to: "page.getByTestId('patientSelect')",
  },
  'operations.anchor': {
    file: path.join('tests', 'pages', 'operations-page.ts'),
    from: "page.locator('#periodSelect')",
    to: "page.getByTestId('periodSelect')",
  },
  'scheduling.anchor': {
    file: path.join('tests', 'pages', 'scheduling-kpis-page.ts'),
    from: "page.locator('#trendChart')",
    to: "page.getByTestId('trendChart')",
  },
};

function output(status, details = {}) {
  const payload = { status, ...details };
  fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  fs.writeFileSync(REPORT_PATH, JSON.stringify(payload, null, 2));
  console.log(JSON.stringify(payload, null, 2));
  process.exit(0);
}

function loadAuditor() {
  if (!fs.existsSync(AUDITOR_REPORT)) return null;
  try {
    return JSON.parse(fs.readFileSync(AUDITOR_REPORT, 'utf8') || '{}');
  } catch (_) {
    return null;
  }
}

function main() {
  const auditor = loadAuditor();
  const results = auditor?.results || [];
  const fragile = results.filter((r) => r.status !== 'ok');

  const changes = [];

  for (const item of fragile) {
    const plan = REPLACEMENTS[item.key];
    if (!plan) continue;
    const filePath = path.resolve(plan.file);
    if (!fs.existsSync(filePath)) {
      changes.push({ key: item.key, action: 'skip', reason: 'file-missing', file: plan.file });
      continue;
    }
    const content = fs.readFileSync(filePath, 'utf8');
    if (!content.includes(plan.from)) {
      changes.push({ key: item.key, action: 'skip', reason: 'selector-not-found', file: plan.file });
      continue;
    }
    const updated = content.replace(plan.from, plan.to);
    fs.writeFileSync(filePath, updated, 'utf8');
    changes.push({ key: item.key, action: 'refactored', from: plan.from, to: plan.to, file: plan.file });
  }

  const refactored = changes.filter((c) => c.action === 'refactored');
  const status = refactored.length ? 'refactored' : 'noop';
  const recommendation = 'Run E2E tests again';

  output(status, { changes, recommendation });
}

main();