#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const STORAGE_PATH = process.env.STORAGE_PATH || path.join('tests', 'fixtures', 'storageState.json');
const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const FAULT_SCENARIO = String(process.env.FAULT_SCENARIO || '').trim();

const SELECTORS = [
  { key: 'calendar.anchor', path: '/praxi_backend/appointments/', selector: '#appointmentCalendar' },
  { key: 'patients.anchor', path: '/praxi_backend/patients/', selector: '#patientsTable, #patientSelect' },
  { key: 'operations.anchor', path: '/praxi_backend/operations/', selector: '#periodSelect' },
  { key: 'scheduling.anchor', path: '/praxi_backend/scheduling/', selector: '#trendChart' },
];

// When FAULT_SCENARIO=selector, also audit test-injected broken selectors to detect test-locator faults.
const FAULT_SELECTOR_OVERRIDES = {
  selector: [
    { key: 'calendar.anchor.fault', path: '/praxi_backend/appointments/', selector: '#appointmentCalendarBROKEN' },
  ],
};

function output(status, details = {}, exitCode = 0) {
  const payload = { status, ...details };
  console.log(JSON.stringify(payload, null, 2));
  process.exit(exitCode);
}

function ensureStorage() {
  if (!fs.existsSync(STORAGE_PATH)) {
    output('error', { reason: 'missing-storage', storagePath: STORAGE_PATH }, 1);
  }
}

async function auditItems(browser, context, items) {
  const results = [];
  for (const item of items) {
    const page = await context.newPage();
    let count = 0;
    let httpStatus = 0;
    try {
      const resp = await page.goto(item.path);
      httpStatus = resp ? resp.status() : 0;
      await page.waitForLoadState('networkidle');
      count = await page.locator(item.selector).count();
    } catch (err) {
      results.push({ key: item.key, selector: item.selector, status: 'error', message: err.message });
      await page.close();
      continue;
    }

    const status = count > 0 ? 'ok' : 'missing';
    const recommendation = count > 0 ? '' : `Consider data-testid="${item.key}" for stability.`;
    results.push({ key: item.key, selector: item.selector, status, httpStatus, count, recommendation });
    await page.close();
  }
  return results;
}

async function audit() {
  ensureStorage();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ baseURL: BASE_URL, storageState: STORAGE_PATH });

  const results = await auditItems(browser, context, SELECTORS);

  let faultResults = [];
  if (FAULT_SCENARIO === 'selector') {
    const faultItems = FAULT_SELECTOR_OVERRIDES[FAULT_SCENARIO] || [];
    faultResults = await auditItems(browser, context, faultItems);
    const faultMissing = faultResults.filter((r) => r.status !== 'ok');
    if (faultMissing.length > 0) {
      await context.close();
      await browser.close();
      output('error', {
        reason: 'fault-selector-missing',
        faultScenario: FAULT_SCENARIO,
        results,
        faultResults,
        message: 'Test-locator fault detected: fault-injected selectors are missing (expected for FAULT_SCENARIO=selector).',
      }, 1);
    }
  }

  await context.close();
  await browser.close();

  const missing = results.filter((r) => r.status !== 'ok');
  if (missing.length) {
    output('error', {
      results,
      ...(faultResults.length ? { faultResults, faultScenario: FAULT_SCENARIO } : {}),
    }, 1);
  }

  output('ok', {
    results,
    ...(faultResults.length ? { faultResults, faultScenario: FAULT_SCENARIO } : {}),
  }, 0);
}

audit().catch((err) => {
  console.error(err);
  output('error', { reason: 'exception', message: err.message }, 1);
});
