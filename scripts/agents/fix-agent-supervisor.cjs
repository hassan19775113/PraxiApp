#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = process.env.AGENT_OUTPUT_DIR || 'agent-outputs';
const SELF_HEAL_CONTEXT_PATH = process.env.SELF_HEAL_CONTEXT_PATH || 'self-heal/context.json';

const FILES = {
  auth: 'auth-validator.json',
  seed: 'seed-orchestrator.json',
  smoke: 'page-smoke.json',
  flaky: 'flaky-classifier.json',
  selector: 'selector-auditor.json',
};

function computeDashboardUrl() {
  const repo = process.env.GITHUB_REPOSITORY;
  if (!repo) return null;
  const [owner, repoName] = repo.split('/');
  if (!owner || !repoName) return null;
  return `https://${owner}.github.io/${repoName}/dashboard.html`;
}

function computeBadgeUrl() {
  const repo = process.env.GITHUB_REPOSITORY;
  if (!repo) return null;
  const [owner, repoName] = repo.split('/');
  if (!owner || !repoName) return null;
  return `https://${owner}.github.io/${repoName}/badge.svg`;
}

function output(status, details = {}, exitCode = 0) {
  const payload = { status, ...details };
  console.log(JSON.stringify(payload, null, 2));
  process.exit(exitCode);
}

function readJson(name) {
  const p = path.join(OUTPUT_DIR, name);
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8') || '{}');
  } catch (err) {
    return { status: 'error', reason: 'parse', message: err.message };
  }
}

function readClassification() {
  if (!fs.existsSync(SELF_HEAL_CONTEXT_PATH)) return null;
  try {
    const ctx = JSON.parse(fs.readFileSync(SELF_HEAL_CONTEXT_PATH, 'utf8') || '{}');
    return ctx?.analysis?.classification ?? null;
  } catch {
    return null;
  }
}

const TEST_CODE_FAULT_TYPES = new Set(['frontend-selector', 'frontend-availability', 'api-404']);
const MANUAL_ONLY_TYPES = new Set(['unknown', 'missing_logs']);

function decide() {
  const auth = readJson(FILES.auth);
  const seed = readJson(FILES.seed);
  const smoke = readJson(FILES.smoke);
  const flaky = readJson(FILES.flaky);
  const selector = readJson(FILES.selector);

  function isOk(status) {
    return status === 'ok' || status === 'success';
  }

  // 1) Hard blockers: auth/seed/smoke
  if (!auth || !isOk(auth.status) || !seed || !isOk(seed.status) || !smoke || !isOk(smoke.status)) {
    return {
      decision: 'abort',
      reason: 'Prerequisites failed',
      recommendations: ['Fix auth/seed/smoke first'],
      auth,
      seed,
      smoke,
      flaky,
      selector,
    };
  }

  const deterministic = (flaky?.deterministic || []).length;
  const flakyCount = (flaky?.flaky || []).length;

  // 4) Selector issues
  const selectorProblem = selector && selector.status !== 'ok';
  if (selectorProblem) {
    return {
      decision: 'needs-selector-refactor',
      reason: 'Selector issues detected',
      recommendations: ['Run Selector-Refactor Agent'],
      auth,
      seed,
      smoke,
      flaky,
      selector,
    };
  }

  // 2) Only flaky failures
  if (flakyCount > 0 && deterministic === 0) {
    return {
      decision: 'abort',
      reason: 'Only flaky tests detected',
      recommendations: ['Stabilize waits/selectors before healing'],
      auth,
      seed,
      smoke,
      flaky,
      selector,
    };
  }

  // 3) Deterministic failures present: route by classification
  if (deterministic > 0) {
    const classification = readClassification();
    const errorType = classification?.error_type;
    if (errorType && MANUAL_ONLY_TYPES.has(errorType)) {
      return {
        decision: 'manual-review',
        reason: 'Classification is unknown or logs are missing; skip autonomous repair',
        recommendations: ['Collect richer logs and retry classification before applying fixes'],
        classification: { error_type: errorType },
        auth,
        seed,
        smoke,
        flaky,
        selector,
      };
    }
    if (errorType && TEST_CODE_FAULT_TYPES.has(errorType)) {
      return {
        decision: 'run-fix-agent',
        reason: 'Test-code fault detected (structural fix required)',
        recommendations: ['Fix-Agent will apply targeted patch for selector/availability/API URL'],
        classification: { error_type: errorType },
        auth,
        seed,
        smoke,
        flaky,
        selector,
      };
    }
    return {
      decision: 'run-self-heal',
      reason: 'Deterministic failures detected (environment/transient)',
      recommendations: ['Trigger Self-Heal Agent with patch generation'],
      auth,
      seed,
      smoke,
      flaky,
      selector,
    };
  }

  // Default: all green
  return {
    decision: 'ok',
    reason: 'All tests passed',
    recommendations: [],
    auth,
    seed,
    smoke,
    flaky,
    selector,
  };
}

function main() {
  const agg = decide();
  const dashboardUrl = computeDashboardUrl();
  const badgeUrl = computeBadgeUrl();
  const payload = { ...agg, dashboardUrl, badgeUrl };
  const decisionPath = path.join(OUTPUT_DIR, 'supervisor-decision.json');
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(decisionPath, JSON.stringify(payload, null, 2));

  // Exit code 0 always, supervisor is advisory; decision carries state.
  output('ok', payload, 0);
}

main();