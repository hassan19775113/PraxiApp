import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

type JsonResponse = {
  statusCode?: number;
  setHeader?: (name: string, value: string) => void;
  end?: (body?: string) => void;
};

type JsonRequest = {
  method?: string;
  headers?: Record<string, string | string[] | undefined>;
  body?: unknown;
  on?: (event: 'data' | 'end' | 'error', cb: (chunk?: any) => void) => void;
};

type ProcessLogsPayload = {
  playwright_log: string;
  backend_log: string;
  run_id: string | number;
  job_name: string;
  timestamp: string;
  branch: string;
  commit: string;
  status: string;
};

type ValidationResult =
  | { ok: true; value: ProcessLogsPayload }
  | { ok: false; errors: string[] };

function timingSafeEqualString(a: string, b: string): boolean {
  const aBuf = Buffer.from(a, 'utf8');
  const bBuf = Buffer.from(b, 'utf8');
  if (aBuf.length !== bBuf.length) return false;
  return crypto.timingSafeEqual(aBuf, bBuf);
}

function getBearerToken(headerValue: string | undefined): string | null {
  if (!headerValue) return null;
  const match = headerValue.match(/^Bearer\s+(.+)$/i);
  return match?.[1]?.trim() || null;
}

function sendJson(res: JsonResponse, statusCode: number, data: unknown) {
  const body = JSON.stringify(data);
  res.statusCode = statusCode;
  res.setHeader?.('Content-Type', 'application/json; charset=utf-8');
  res.end?.(body);
}

async function readJsonBody(req: JsonRequest): Promise<unknown> {
  if (req.body !== undefined) {
    if (typeof req.body === 'string') {
      if (!req.body.trim()) return undefined;
      return JSON.parse(req.body);
    }
    return req.body;
  }

  const chunks: Buffer[] = [];
  await new Promise<void>((resolve, reject) => {
    if (!req.on) return resolve();
    req.on('data', (chunk) => chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(String(chunk))));
    req.on('end', () => resolve());
    req.on('error', (err) => reject(err));
  });

  if (chunks.length === 0) return undefined;
  const raw = Buffer.concat(chunks).toString('utf8');
  if (!raw.trim()) return undefined;
  return JSON.parse(raw);
}

function validatePayload(body: unknown): ValidationResult {
  const errors: string[] = [];
  if (typeof body !== 'object' || body === null) {
    return { ok: false, errors: ['Body must be a JSON object'] };
  }

  const obj = body as Record<string, unknown>;

  const expectString = (key: keyof ProcessLogsPayload) => {
    if (typeof obj[key as string] !== 'string') errors.push(`${String(key)} must be a string`);
  };

  expectString('playwright_log');
  expectString('backend_log');

  if (!(typeof obj.run_id === 'string' || typeof obj.run_id === 'number')) {
    errors.push('run_id must be a string or number');
  }

  expectString('job_name');
  expectString('timestamp');
  expectString('branch');
  expectString('commit');
  expectString('status');

  if (errors.length > 0) return { ok: false, errors };

  return {
    ok: true,
    value: {
      playwright_log: obj.playwright_log as string,
      backend_log: obj.backend_log as string,
      run_id: obj.run_id as string | number,
      job_name: obj.job_name as string,
      timestamp: obj.timestamp as string,
      branch: obj.branch as string,
      commit: obj.commit as string,
      status: obj.status as string,
    },
  };
}

async function ensureDir(dir: string) {
  await fs.mkdir(dir, { recursive: true });
}

async function writeTextFile(filePath: string, content: string) {
  await ensureDir(path.dirname(filePath));
  await fs.writeFile(filePath, content ?? '', { encoding: 'utf8' });
}

function normalizeRunId(runId: string | number): string {
  const s = String(runId);
  return s.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 128) || 'unknown';
}

function detectFailureCause(playwrightLog: string, backendLog: string) {
  const pl = playwrightLog || '';
  const bl = backendLog || '';

  const signals: Array<{ type: string; match: RegExp }> = [
    { type: 'auth', match: /invalid\s+credentials|login\s+failed|401\b|403\b/i },
    { type: 'selector', match: /strict\s+mode\s+violation|locator\(|waiting for selector|toHaveCount\(/i },
    { type: 'timeout', match: /timeout\s+\d+ms|Test timeout of/i },
    { type: 'navigation', match: /net::ERR_|Navigation\s+timeout|page\.goto/i },
    { type: 'db', match: /database\s+error|psycopg|relation\s+.*\s+does not exist|could not connect/i },
    { type: 'backend_exception', match: /Traceback\s+\(most recent call last\):/i },
  ];

  for (const s of signals) {
    if (s.match.test(pl) || s.match.test(bl)) {
      return { error_type: s.type, confidence: 'high' as const };
    }
  }

  if ((pl && pl.length > 0) || (bl && bl.length > 0)) {
    return { error_type: 'unknown', confidence: 'low' as const };
  }

  return { error_type: 'missing_logs', confidence: 'low' as const };
}

function buildInstructions(errorType: string) {
  const selfHeal = {
    action: 'self_heal',
    hints: [] as string[],
  };

  const fixAgent = {
    action: 'fix_agent',
    hints: [] as string[],
  };

  const pr = {
    action: 'prepare_pr',
    branch: 'ai-fix',
    base: 'main',
    title: `[AI] self-heal: ${errorType}`,
    body: `Automated self-heal instructions for error type: ${errorType}`,
  };

  switch (errorType) {
    case 'auth':
      selfHeal.hints.push('Verify E2E user creation in CI and ensure credentials env vars are set.');
      fixAgent.hints.push('Inspect auth endpoints and storageState generation; confirm session/JWT flow.');
      break;
    case 'selector':
      selfHeal.hints.push('Stabilize strict selectors and prefer role-based locators.');
      fixAgent.hints.push('Update Playwright locators/assertions to be resilient to minor UI changes.');
      break;
    case 'timeout':
      selfHeal.hints.push('Increase deterministic waits via health checks; reduce flaky fixed timeouts.');
      fixAgent.hints.push('Add targeted waiting for API readiness and reduce long-running steps.');
      break;
    case 'navigation':
      selfHeal.hints.push('Check baseURL, server readiness, and networking errors.');
      fixAgent.hints.push('Improve retries for navigation + capture failing responses.');
      break;
    case 'db':
      selfHeal.hints.push('Check migrations/seed and Postgres readiness/credentials.');
      fixAgent.hints.push('Align DB setup steps and validate DATABASE_URL usage.');
      break;
    case 'backend_exception':
      selfHeal.hints.push('Locate traceback in backend log and fix failing code path.');
      fixAgent.hints.push('Write a minimal repro based on traceback; add regression coverage if possible.');
      break;
    default:
      selfHeal.hints.push('Collect more context; ensure artifacts include playwright + backend CI logs.');
      fixAgent.hints.push('Parse logs for the first fatal error and map it to code locations.');
      break;
  }

  return { selfHeal, fixAgent, pr };
}

async function triggerModules(runDir: string, payload: ProcessLogsPayload, analysis: any) {
  const triggersPath = path.join(runDir, 'triggers.json');
  const triggers = {
    triggered_at: new Date().toISOString(),
    status: payload.status,
    triggers: {
      self_heal: payload.status === 'failed',
      fix_agent: payload.status === 'failed',
      pr_instructions: payload.status === 'failed',
    },
    analysis,
  };
  await writeTextFile(triggersPath, JSON.stringify(triggers, null, 2));
}

export default async function handler(req: JsonRequest, res: JsonResponse) {
  if (req.method !== 'POST') {
    res.setHeader?.('Allow', 'POST');
    return sendJson(res, 405, { error: 'Method Not Allowed' });
  }

  const expectedToken = process.env.DEVELOPER_AGENT_TOKEN;
  if (!expectedToken) {
    return sendJson(res, 500, { error: 'Server misconfigured: DEVELOPER_AGENT_TOKEN missing' });
  }

  const headers = req.headers || {};
  const authHeaderValue = Array.isArray(headers.authorization) ? headers.authorization[0] : headers.authorization;
  const presentedToken = getBearerToken(authHeaderValue);
  if (!presentedToken || !timingSafeEqualString(presentedToken, expectedToken)) {
    return sendJson(res, 401, { error: 'Unauthorized' });
  }

  let body: unknown;
  try {
    body = await readJsonBody(req);
  } catch (e) {
    return sendJson(res, 400, { error: 'Invalid JSON body', details: [String(e)] });
  }

  const validated = validatePayload(body);
  if (validated.ok === false) {
    return sendJson(res, 400, { error: 'Invalid payload', details: validated.errors });
  }

  const runId = normalizeRunId(validated.value.run_id);

  const primaryLogsRoot = path.join(process.cwd(), 'logs');
  const fallbackLogsRoot = path.join('/tmp', 'logs');

  let logsRoot = primaryLogsRoot;
  try {
    await ensureDir(logsRoot);
  } catch {
    logsRoot = fallbackLogsRoot;
    await ensureDir(logsRoot);
  }

  const runDir = path.join(logsRoot, runId);

  await writeTextFile(path.join(runDir, 'playwright.log'), validated.value.playwright_log);
  await writeTextFile(path.join(runDir, 'backend.log'), validated.value.backend_log);

  const failureCause = detectFailureCause(validated.value.playwright_log, validated.value.backend_log);
  const instructions = buildInstructions(failureCause.error_type);

  const analysis = {
    processed_at: new Date().toISOString(),
    run_id: runId,
    job_name: validated.value.job_name,
    branch: validated.value.branch,
    commit: validated.value.commit,
    status: validated.value.status,
    failure_cause: failureCause,
    self_heal_instructions: instructions.selfHeal,
    fix_agent_instructions: instructions.fixAgent,
    pr_instructions: instructions.pr,
  };

  await writeTextFile(path.join(runDir, 'analysis.json'), JSON.stringify(analysis, null, 2));

  if (validated.value.status === 'failed') {
    await triggerModules(runDir, validated.value, analysis);
  }

  return sendJson(res, 200, { status: 'processed' });
}
