# Agent-Engine Fault-Handling Pipeline: Targeted Improvements Proposal

**Date:** 2026-02-15  
**Status:** Proposal  
**Scope:** selector-auditor, Cloud Agent, supervisor, self-heal, Fix-Agent, transience detection, process-logs

---

## Executive Summary

This proposal addresses seven improvement areas in the Agent-Engine fault-handling pipeline to close gaps identified in the fault-scenario analysis. Each section includes: current state, proposed changes, and implementation notes.

---

## 1. Selector-Auditor Gap: FAULT_SCENARIO-Aware Auditing

### Current State

- `selector-auditor.cjs` audits **production DOM selectors** only (e.g. `#appointmentCalendar`).
- It does **not** receive `FAULT_SCENARIO`; it runs in `backend-setup.yml` without fault injection.
- Test-locator faults (e.g. `#appointmentCalendarBROKEN` in `calendar-page.ts`) are **invisible** to the auditor because:
  - The auditor checks real page DOM, not test code.
  - The fault lives in Page Object locators, not in the page itself.

### Proposed Changes

**1.1 Pass FAULT_SCENARIO to selector-auditor**

In `agent-engine.yml`, pass `fault_scenario` into the selector-auditor job. This requires extending `backend-setup.yml` to accept an optional `fault_scenario` input and forward it as `FAULT_SCENARIO` env var.

```yaml
# agent-engine.yml - selector-auditor job
selector-auditor:
  uses: ./.github/workflows/backend-setup.yml
  with:
    fault_scenario: ${{ inputs.fault_scenario }}
    agent_command: node scripts/agents/selector-auditor.cjs > agent-outputs/selector-auditor.json
    # ...
```

**1.2 Define test-locator fault mappings**

Add a mapping in `selector-auditor.cjs` that maps `FAULT_SCENARIO=selector` to the **broken** selectors used in tests:

```javascript
// When FAULT_SCENARIO=selector, we audit BOTH production and test-injected selectors
const FAULT_SELECTOR_OVERRIDES = {
  selector: [
    { key: 'calendar.anchor.fault', path: '/praxi_backend/appointments/', selector: '#appointmentCalendarBROKEN' },
    // Add more as fault scenarios expand
  ],
};
```

**1.3 Dual-mode audit**

- **Normal mode** (`FAULT_SCENARIO` empty): Audit production selectors only (current behavior).
- **Fault mode** (`FAULT_SCENARIO=selector`): Also audit fault-injected selectors. If any fault selector is missing (expected), report `status: 'fault-injected'` and include `faultScenario: 'selector'` in output. Supervisor can use this to infer test-locator fault.

**1.4 Output schema extension**

```json
{
  "status": "error",
  "reason": "fault-selector-missing",
  "faultScenario": "selector",
  "results": [...],
  "faultResults": [{ "key": "calendar.anchor.fault", "selector": "#appointmentCalendarBROKEN", "status": "missing" }]
}
```

### Implementation Notes

- Add `fault_scenario` input to `backend-setup.yml` (optional, default `''`).
- In `backend-setup.yml`, set `FAULT_SCENARIO: ${{ inputs.fault_scenario }}` in the agent command step.
- Keep backward compatibility: when `fault_scenario` is empty, auditor behaves as today.

---

## 2. Cloud Agent Classification: New Categories

### Current State

- `api/process-logs.ts` classifies into: `frontend-selector`, `frontend-timing`, `infra/network`, `auth/session`, `backend-*`, `unknown`.
- **Availability/API URL** failures (e.g. `/api/availabilityBROKEN/` 404) fall to `unknown` or may match `infra/network` if connection errors appear.

### Proposed Changes

**2.1 Add `frontend-availability`**

For failures where:
- Playwright log mentions availability API, `waitForResponse`, or `availability check failed`.
- Response status 404/500 on an API URL containing `availability`.

```typescript
const availability = /availability\s+check\s+failed|waitForResponse.*availability|/api/availability[^/]*\?|availabilityBROKEN/i;
const api404 = /\b404\b|Not Found|Failed to fetch|fetch\s+failed/i;
```

**2.2 Add `api-404` (generic API endpoint mismatch)**

For:
- 404 on API URLs.
- `Failed to check availability`, `UI availability check failed`, similar patterns.

**2.3 Classification order**

Run **availability/api-404** checks **before** generic `selector` and `timing` to avoid false positives (e.g. selector regex matching "availability" in a different context).

Suggested order in `classifyFailure()`:

1. backend-migration, backend-traceback, backend-500
2. auth/session
3. **frontend-availability** (new)
4. **api-404** (new)
5. infra/network
6. frontend-selector
7. frontend-timing
8. unknown

### Implementation Notes

- Add types to `Classification.error_type` union.
- Add `buildSelfHealPlan` and `buildFixAgentInstructions` branches for new types.
- Ensure `decide.mjs` and `apply-and-validate.mjs` handle new types.

---

## 3. Supervisor Logic: Differentiate Test-Code vs Environment Faults

### Current State

- Supervisor receives: auth, seed, smoke, flaky, selector.
- It does **not** receive Cloud Agent classification.
- Decision flow: prerequisites → selector problem → flaky-only → deterministic → ok.
- **Gap:** Deterministic + selector-auditor ok → `run-self-heal` even when the fault is in **test code** (e.g. wrong locator), not environment.

### Proposed Changes

**3.1 Pass classification to supervisor**

- `prepare-context.mjs` and `prepare-input.mjs` produce context/input with `analysis.classification`.
- Supervisor runs **after** startup-fix-agent (which produces context). But supervisor does not download or read that context.
- **Option A:** Add a job that writes `classification.json` from context to an artifact; supervisor downloads it.
- **Option B:** Supervisor downloads `self-heal-context` artifact and reads `context.json` to get `analysis.classification`.

**3.2 New decision branch: test-code fault**

When `classification.error_type` is one of:
- `frontend-selector`
- `frontend-availability`
- `api-404`

→ Treat as **test-code fault** (structural, not transient). Decision: `run-fix-agent` instead of `run-self-heal`.

**3.3 Updated decision matrix**

| Prerequisites | Selector auditor | Flaky | Deterministic | Classification        | Decision                  |
|--------------|------------------|-------|---------------|----------------------|---------------------------|
| fail         | -                | -     | -             | -                    | abort                     |
| ok           | fail             | -     | -             | -                    | needs-selector-refactor   |
| ok           | ok               | >0    | 0             | -                    | abort                     |
| ok           | ok               | -     | >0            | test-code fault*     | **run-fix-agent** (new)   |
| ok           | ok               | -     | >0            | env/transient fault  | run-self-heal             |
| ok           | ok               | -     | 0             | -                    | ok                        |

\* test-code fault: `frontend-selector`, `frontend-availability`, `api-404`

**3.4 Fallback when classification is missing**

If `classification` is null or `unknown`, keep current behavior: `run-self-heal` for deterministic. Self-heal's `decide.mjs` will deny for `unknown` anyway.

### Implementation Notes

- Supervisor needs access to classification. Easiest: download `self-heal-context` (or a new `classification` artifact) in fix-agent-supervisor job.
- Add `run-fix-agent` as a new decision value.
- Downstream jobs (e.g. ci-dashboard-agent) may need to handle `run-fix-agent` in addition to `run-self-heal`.

---

## 4. Self-Heal Decision Rules: Consistent Routing

### Current State

- `allowedForSelfHeal`: only `infra/network`, `frontend-timing`, `auth/session`.
- `frontend-selector`, `frontend-availability`, `unknown` → denied.

### Proposed Changes

**4.1 Explicit deny list**

Make the deny list explicit for clarity:

```javascript
const SELF_HEAL_DENIED = new Set([
  'frontend-selector',
  'frontend-availability',
  'api-404',
  'backend-migration',
  'backend-exception',
  'backend-500',
  'unknown',
  'missing_logs',
]);

function allowedForSelfHeal(errorType) {
  return !SELF_HEAL_DENIED.has(errorType) && 
    ['infra/network', 'frontend-timing', 'auth/session'].includes(errorType);
}
```

**4.2 Refine `frontend-timing`**

- **Problem:** `frontend-timing` is allowed for self-heal, but injected timeout (60s sleep) is deterministic. Reseed+rerun will fail again.
- **Proposal:** Add transience hint (see Section 6). If transience is `low`, do **not** allow self-heal for `frontend-timing`.

**4.3 Add `frontend-availability` and `api-404` to Fix-Agent routing**

Ensure `decide.mjs` explicitly denies these and recommends Fix-Agent:

```javascript
recommendations_for_fix_agent: [
  'Use Fix-Agent for code changes; self-heal skipped by policy.',
  'Error type requires structural fix (selector/API URL).',
],
```

---

## 5. Fix-Agent: Actionable Instructions for Availability/API URL

### Current State

- `apply-and-validate.mjs` handles `frontend-selector` and `frontend-timing` only.
- `frontend-availability` and `api-404` would fall through to `metadata.allowed = false` (no classification/instructions).

### Proposed Changes

**5.1 Add `frontend-availability` handling**

In `buildFixAgentInstructions` (process-logs.ts):

```typescript
case 'frontend-availability':
  direction = 'Fix availability API URL or mock; ensure tests use correct endpoint (/api/availability/).';
  suspectedPaths.push('tests/pages/');
  suspectedPaths.push('tests/e2e/');
  break;
```

**5.2 Add `api-404` handling**

```typescript
case 'api-404':
  direction = 'Fix API endpoint URL in test or page object; verify route exists in backend.';
  suspectedPaths.push('tests/');
  suspectedPaths.push('django/apps/');
  break;
```

**5.3 Fix-Agent apply-and-validate**

Add a transform for `frontend-availability` / `api-404`:

- **Pattern:** Extract URL from log (e.g. `/api/availabilityBROKEN/`).
- **Fix:** Search for the wrong URL in `tests/` and `django/` and suggest correction (e.g. `availabilityBROKEN` → `availability`).
- **Guardrail:** Only apply if the fix is a simple string replacement (typo fix), not structural changes.

```javascript
function extractWrongApiUrl(playwrightSnippet) {
  const re = /\/api\/([a-zA-Z0-9_-]+BROKEN)\/?/;
  const m = playwrightSnippet.match(re);
  return m ? m[1] : null;
}
```

If `availabilityBROKEN` is found, replace with `availability` in the matching file.

---

## 6. Transience-Detection Heuristics

### Current State

- `inferTransientLikelihood`: `frontend-timing` → `high`, others → `low`/`medium`.
- No use of flaky-classifier output (deterministic vs flaky) in self-heal decision.
- Reseed+rerun runs even for deterministic failures, wasting CI time.

### Proposed Changes

**6.1 Pass flaky-classifier result to self-heal context**

- `prepare-context.mjs` currently does not receive flaky-classifier output.
- **Proposal:** Add a step in startup-fix-agent (or a preceding job) that downloads `flaky-classifier-output` and merges `deterministic: [...], flaky: [...]` into context.

**6.2 Transience heuristic**

```javascript
function inferTransientLikelihood(errorType, context) {
  const deterministic = (context?.flaky?.deterministic || []).length;
  const flaky = (context?.flaky?.flaky || []).length;

  // If all failures are deterministic, treat as low transience
  if (deterministic > 0 && flaky === 0) {
    return 'low';
  }
  if (flaky > 0) {
    return 'high';
  }

  switch (errorType) {
    case 'infra/network':
    case 'auth/session':
      return 'medium';
    case 'frontend-timing':
      return 'high'; // Only if we have flaky; otherwise low from above
    default:
      return 'low';
  }
}
```

**6.3 Skip self-heal when transience is low**

```javascript
function allowedForSelfHeal(errorType, context) {
  if (SELF_HEAL_DENIED.has(errorType)) return false;
  const transient = inferTransientLikelihood(errorType, context);
  if (transient === 'low') return false;  // Don't waste reseed+rerun
  return ['infra/network', 'frontend-timing', 'auth/session'].includes(errorType);
}
```

**6.4 Implementation**

- `prepare-context.mjs` needs to read `flaky-classifier-output` from artifacts. Currently it runs in a job that downloads E2E artifacts only. Add download of `flaky-classifier-output` to startup-fix-agent.
- `decide.mjs` receives context; add `context.flaky` and use it in `inferTransientLikelihood` and `allowedForSelfHeal`.

---

## 7. Log-Pattern Matching in process-logs.ts

### Current State

- Patterns are broad; order matters (first match wins).
- `selector` matches `locator(`, `toBeVisible(` — can overlap with timing.
- `timing` matches `expect(.+).to` — very broad, may match many failures.

### Proposed Changes

**7.1 Tighten selector pattern**

```typescript
// Before: /strict\s+mode\s+violation|waiting for selector|locator\(|toHaveCount\(|toBeVisible\(/i
// After: More specific, avoid overlap with timing
const selector = /strict\s+mode\s+violation|waiting\s+for\s+selector\s+['"`#]|locator\(['"`][^'"`]+['"`]\)\s+resolved\s+to\s+\d+\s+element/i;
```

Keep `toHaveCount` and `toBeVisible` but only when co-occurring with selector-like context (e.g. "Locator resolved to 0 elements").

**7.2 Tighten timing pattern**

```typescript
// Before: /Test timeout of|Timeout \d+ms exceeded|expect\(.+\)\.to/i
// After: Focus on timeout signals; avoid generic expect
const timing = /Test\s+timeout\s+of\s+\d+\s*ms|Timeout\s+\d+\s*ms\s+exceeded|waitForTimeout|exceeded\s+while\s+waiting/i;
```

**7.3 Add availability pattern**

```typescript
const availability = /availability\s+check\s+failed|UI\s+availability\s+check\s+failed|/api\/availability[^/\s]*\?|availabilityBROKEN|Failed\s+to\s+check\s+availability/i;
```

**7.4 Add API 404 pattern**

```typescript
const api404 = /\b404\b.*\/api\/|Not\s+Found.*\/api\/|Failed\s+to\s+fetch|fetch\s+failed|status[:\s]404/i;
```

**7.5 Disambiguation**

When both selector and timing could match, use **confidence** and **context**:

- If "strict mode violation" present → prefer `frontend-selector`.
- If "Test timeout of Xms" present → prefer `frontend-timing`.
- If "availability" + "404" or "failed" → prefer `frontend-availability` or `api-404`.

**7.6 Multi-signal scoring (optional)**

Instead of first-match-wins, score each pattern and pick highest:

```typescript
const scores = [
  { type: 'frontend-selector', score: selectorScore(pl) },
  { type: 'frontend-timing', score: timingScore(pl) },
  { type: 'frontend-availability', score: availabilityScore(pl) },
  // ...
];
const best = scores.filter(s => s.score > 0).sort((a, b) => b.score - a.score)[0];
return best?.type ?? 'unknown';
```

---

## Implementation Priority

| # | Improvement                    | Effort | Impact | Priority |
|---|--------------------------------|--------|--------|----------|
| 1 | process-logs.ts patterns      | Low    | High   | P0       |
| 2 | Cloud Agent new categories    | Low    | High   | P0       |
| 3 | Self-heal deny list + routing | Low    | Medium | P1       |
| 4 | Fix-Agent availability/404    | Medium | High   | P1       |
| 5 | Transience heuristics         | Medium | Medium | P2       |
| 6 | Supervisor + classification   | Medium | High   | P2       |
| 7 | Selector-auditor FAULT_SCENARIO | Medium | Medium | P2       |

---

## Files to Modify

| File                         | Changes                                                                 |
|------------------------------|-------------------------------------------------------------------------|
| `api/process-logs.ts`        | New types, patterns, buildSelfHealPlan, buildFixAgentInstructions        |
| `tools/self-heal/decide.mjs` | Deny list, transience heuristic, flaky in context                       |
| `tools/fix-agent/apply-and-validate.mjs` | frontend-availability, api-404 handling, URL fix transform      |
| `scripts/agents/selector-auditor.cjs` | FAULT_SCENARIO, fault selector overrides, dual-mode audit        |
| `scripts/agents/fix-agent-supervisor.cjs` | Classification input, run-fix-agent decision branch              |
| `.github/workflows/backend-setup.yml` | fault_scenario input, FAULT_SCENARIO env                      |
| `.github/workflows/agent-engine.yml` | Pass fault_scenario to selector-auditor, supervisor artifact deps |
| `tools/self-heal/prepare-context.mjs` | Download flaky-classifier artifact, merge into context          |

---

**End of Proposal**
