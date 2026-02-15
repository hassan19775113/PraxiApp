#!/usr/bin/env node

import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const APPLY_SCRIPT = path.join(REPO_ROOT, 'tools', 'fix-agent', 'apply-and-validate.mjs');

function run(cmd, args, cwd, env = {}) {
  const res = spawnSync(cmd, args, {
    cwd,
    env: { ...process.env, ...env },
    encoding: 'utf8',
  });
  return {
    code: res.status ?? 1,
    stdout: res.stdout || '',
    stderr: res.stderr || '',
  };
}

async function ensureFile(filePath, content) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content, 'utf8');
}

async function readJson(filePath) {
  const raw = await fs.readFile(filePath, 'utf8');
  return JSON.parse(raw);
}

async function setupTempRepo() {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'fix-agent-fs-'));
  const gitInit = run('git', ['init'], tmp);
  if (gitInit.code !== 0) throw new Error(`git init failed: ${gitInit.stderr}`);
  run('git', ['config', 'user.name', 'test-bot'], tmp);
  run('git', ['config', 'user.email', 'test-bot@example.com'], tmp);
  return tmp;
}

async function commitBaseline(tmp) {
  const add = run('git', ['add', '.'], tmp);
  if (add.code !== 0) throw new Error(`git add failed: ${add.stderr}`);
  const commit = run('git', ['commit', '-m', 'baseline'], tmp);
  if (commit.code !== 0) throw new Error(`git commit failed: ${commit.stderr}`);
}

async function runApply(tmp, inputObj, runId = '1') {
  const inputPath = path.join(tmp, 'fix-agent', 'input.json');
  const outDir = path.join(tmp, 'fix-agent');
  await ensureFile(inputPath, `${JSON.stringify({ run_id: runId, ...inputObj }, null, 2)}\n`);

  const exec = run(
    'node',
    [APPLY_SCRIPT, '--input', inputPath, '--out-dir', outDir],
    tmp,
    { GITHUB_RUN_ID: runId },
  );
  if (exec.code !== 0) {
    throw new Error(`apply-and-validate failed (${exec.code}): ${exec.stderr || exec.stdout}`);
  }

  const patchPath = path.join(outDir, `patch-${runId}.diff`);
  const metadataPath = path.join(outDir, `metadata-${runId}.json`);
  const patch = await fs.readFile(patchPath, 'utf8').catch(() => '');
  const metadata = await readJson(metadataPath);
  return { patch, metadata };
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function testFs1NonStrictSelector() {
  const tmp = await setupTempRepo();
  await ensureFile(
    path.join(tmp, 'tests', 'pages', 'calendar-page.ts'),
    [
      "import { test } from '@playwright/test';",
      "export function demo(page) {",
      "  return page.locator('#appointmentCalendarBROKEN');",
      '}',
      '',
    ].join('\n'),
  );
  await commitBaseline(tmp);

  const { patch, metadata } = await runApply(
    tmp,
    {
      logs: { extracted_spec_paths: [] },
      analysis: {
        classification: { error_type: 'frontend-selector' },
        fix_agent_instructions: {
          suspected_paths: ['tests/pages/calendar-page.ts'],
          failing_tests: ['calendar selector test'],
          key_log_snippets: {
            playwright: "Error: waiting for selector '#appointmentCalendarBROKEN'",
            backend: '',
          },
        },
      },
    },
    '101',
  );

  assert(patch.includes(".first()"), 'FS-1 failed: expected non-strict selector to be patched with .first()');
  assert(metadata.change_summary.changed_files.length > 0, 'FS-1 failed: expected changed files');
}

async function testFs2DeterministicTiming() {
  const tmp = await setupTempRepo();
  await ensureFile(
    path.join(tmp, 'tests', 'e2e', 'appointment-modal.spec.ts'),
    [
      "import { test } from '@playwright/test';",
      'test("timing", async ({ page }) => {',
      '  await page.waitForTimeout(60000);',
      '});',
      '',
    ].join('\n'),
  );
  await commitBaseline(tmp);

  const { patch, metadata } = await runApply(
    tmp,
    {
      logs: { extracted_spec_paths: [] },
      analysis: {
        classification: { error_type: 'frontend-timing' },
        fix_agent_instructions: {
          suspected_paths: ['tests/e2e/appointment-modal.spec.ts'],
          failing_tests: ['timing test'],
          key_log_snippets: {
            playwright: 'Test timeout of 30000ms exceeded; waitForTimeout(60000)',
            backend: '',
          },
        },
      },
    },
    '102',
  );

  assert(patch.includes('test.setTimeout(60000);'), 'FS-2 failed: expected test.setTimeout insertion');
  assert(patch.includes('waitForTimeout(500)'), 'FS-2 failed: expected excessive waitForTimeout reduction');
  assert(metadata.change_summary.changed_files.length > 0, 'FS-2 failed: expected changed files');
}

async function testFs3AvailabilityNonBrokenTypo() {
  const tmp = await setupTempRepo();
  await ensureFile(
    path.join(tmp, 'tests', 'pages', 'appointment-modal-page.ts'),
    [
      "export function url() {",
      "  return '/api/availabilty/?start=a&end=b';",
      '}',
      '',
    ].join('\n'),
  );
  await commitBaseline(tmp);

  const { patch } = await runApply(
    tmp,
    {
      logs: { extracted_spec_paths: [] },
      analysis: {
        classification: { error_type: 'frontend-availability' },
        fix_agent_instructions: {
          suspected_paths: ['tests/pages/appointment-modal-page.ts'],
          failing_tests: ['availability test'],
          key_log_snippets: {
            playwright: 'UI availability check failed: 404 GET /api/availabilty/?start=...&end=...',
            backend: '',
          },
        },
      },
    },
    '103',
  );

  assert(patch.includes('/api/availability/'), 'FS-3 failed: expected typo correction to /api/availability/');
}

async function testFs4Api404NonBrokenTypo() {
  const tmp = await setupTempRepo();
  await ensureFile(
    path.join(tmp, 'tests', 'e2e', 'api.spec.ts'),
    [
      "export const endpoint = '/api/appoitments/';",
      '',
    ].join('\n'),
  );
  await commitBaseline(tmp);

  const { patch } = await runApply(
    tmp,
    {
      logs: { extracted_spec_paths: [] },
      analysis: {
        classification: { error_type: 'api-404' },
        fix_agent_instructions: {
          suspected_paths: ['tests/e2e/api.spec.ts'],
          failing_tests: ['api 404 test'],
          key_log_snippets: {
            playwright: 'GET /api/appoitments/ -> 404 Not Found',
            backend: '',
          },
        },
      },
    },
    '104',
  );

  assert(patch.includes('/api/appointments/'), 'FS-4 failed: expected typo correction to /api/appointments/');
}

async function testFs5UnknownMetadataOnly() {
  const tmp = await setupTempRepo();
  await ensureFile(path.join(tmp, 'tests', 'e2e', 'dummy.spec.ts'), "export const x = 'y';\n");
  await commitBaseline(tmp);

  const { patch, metadata } = await runApply(
    tmp,
    {
      logs: { extracted_spec_paths: ['tests/e2e/dummy.spec.ts'] },
      analysis: {
        classification: { error_type: 'unknown' },
        fix_agent_instructions: {
          suspected_paths: ['tests/e2e/dummy.spec.ts'],
          failing_tests: ['unknown failing test'],
          key_log_snippets: {
            playwright: 'some unmatched failure',
            backend: '',
          },
        },
      },
    },
    '105',
  );

  assert(patch.trim() === '', 'FS-5 failed: expected empty patch for unknown classification');
  assert(metadata.needs_manual_review === true, 'FS-5 failed: expected needs_manual_review=true');
  assert(metadata.allowed === false, 'FS-5 failed: expected allowed=false');
  assert(metadata.hints && metadata.hints.playwright_snippet, 'FS-5 failed: expected metadata hints');
}

async function main() {
  const tests = [
    ['FS-1 non-strict selector', testFs1NonStrictSelector],
    ['FS-2 deterministic timing', testFs2DeterministicTiming],
    ['FS-3 availability non-BROKEN', testFs3AvailabilityNonBrokenTypo],
    ['FS-4 api-404 non-BROKEN', testFs4Api404NonBrokenTypo],
    ['FS-5 unknown metadata-only', testFs5UnknownMetadataOnly],
  ];

  let passed = 0;
  for (const [name, fn] of tests) {
    try {
      await fn();
      passed += 1;
      console.log(`PASS ${name}`);
    } catch (err) {
      console.error(`FAIL ${name}: ${String(err?.message || err)}`);
    }
  }

  console.log(`\n${passed}/${tests.length} scenarios passed`);
  process.exit(passed === tests.length ? 0 : 1);
}

main().catch((err) => {
  console.error(String(err?.stack || err));
  process.exit(1);
});

