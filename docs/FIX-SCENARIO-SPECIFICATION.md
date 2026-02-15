# Fix Scenario Specification: Complete Matrix & Generated Scenarios

**Date:** 2026-02-15  
**Purpose:** Verify every detected error type has a corresponding fix scenario; produce concrete specs for missing/partial cases.

---

## Complete Matrix: Detected Error Type → Existing Fix → Missing Fix → Newly Generated Fix Scenario

| Error Type | Existing Fix | Status | Missing Fix | Newly Generated Fix Scenario |
|------------|--------------|--------|-------------|-----------------------------|
| **frontend-selector (strict)** | addFirstForStrictLocator | ✅ Complete | — | — |
| **frontend-selector (non-strict)** | — | ❌ Missing | Extract selector from "waiting for selector" / "element not found" | **FS-1** below |
| **frontend-timing (transient)** | addFileLevelTimeoutIfMissing | ⚠️ Partial | — | — |
| **frontend-timing (deterministic)** | addFileLevelTimeoutIfMissing | ⚠️ Partial | Remove injected waitForTimeout | **FS-2** below |
| **frontend-availability (BROKEN)** | fixWrongApiUrlInSource | ✅ Complete | — | — |
| **frontend-availability (non-BROKEN)** | — | ❌ Missing | Extract wrong URL from 404/failed response | **FS-3** below |
| **api-404 (BROKEN)** | fixWrongApiUrlInSource | ✅ Complete | — | — |
| **api-404 (non-BROKEN)** | — | ❌ Missing | Extract wrong path from log, suggest correction | **FS-4** below |
| **infra/network** | Self-heal only | ⚠️ No code fix | — | **Cannot auto-repair** (see below) |
| **auth/session** | Self-heal only | ⚠️ No code fix | — | **Cannot auto-repair** (see below) |
| **backend-migration** | — | ❌ Missing | — | **Cannot auto-repair** (see below) |
| **backend-exception** | — | ❌ Missing | — | **Cannot auto-repair** (see below) |
| **backend-500** | — | ❌ Missing | — | **Cannot auto-repair** (see below) |
| **unknown** | — | ❌ Missing | Fallback to generic hints | **FS-5** below |
| **missing_logs** | — | ❌ Missing | — | **Cannot auto-repair** (see below) |

---

## Newly Generated Fix Scenarios (Concrete Specs)

### FS-1: frontend-selector (non-strict)

| Field | Specification |
|-------|---------------|
| **Classification** | `frontend-selector` (subtype: `non-strict` via signal) |
| **Detection signals** | `waiting for selector`, `element not found`, `Locator resolved to 0`, `Timeout.*locator`, `#id` or `.class` in error |
| **Fix-agent instructions** | `suspected_paths: [tests/e2e/, tests/pages/]`, `direction: "Extract failing selector from log; add .first() or suggest data-testid"` |
| **Safe code-transform strategy** | 1) Extract selector from log via regex: `locator\(['"]([^'"]+)['"]\)|selector:\s*['"]([^'"]+)['"]|waiting for selector\s+['"]([^'"]+)['"]`; 2) Search suspected files for exact selector string; 3) If found, apply `addFirstForStrictLocator`; 4) If not found, emit hint JSON only (no patch). Guardrail: max 3 selectors, only in tests/ |
| **Validation rules** | Rerun failing spec subset; patch applied only if selector appears in source; no backend changes |

---

### FS-2: frontend-timing (deterministic)

| Field | Specification |
|-------|---------------|
| **Classification** | `frontend-timing` (transience=low from flaky-classifier) |
| **Detection signals** | `waitForTimeout`, `Test timeout of`, `Timeout Xms exceeded` + flaky.deterministic.length > 0 |
| **Fix-agent instructions** | `direction: "Remove or reduce injected waitForTimeout; add test.setTimeout only if truly needed"` |
| **Safe code-transform strategy** | 1) Search for `waitForTimeout(` in spec paths; 2) If found and value > 5000, replace with `waitForTimeout(500)` or remove; 3) Add `test.setTimeout(60000)` only if no existing timeout. Guardrail: never remove legitimate waits < 2s |
| **Validation rules** | Rerun spec; test must pass without 60s sleep; diff size ≤ 5 lines per file |

---

### FS-3: frontend-availability (non-BROKEN)

| Field | Specification |
|-------|---------------|
| **Classification** | `frontend-availability` |
| **Detection signals** | `availability check failed`, `404`, `Failed to fetch`, `/api/` in URL, response status in log |
| **Fix-agent instructions** | `suspected_paths: [tests/pages/, tests/e2e/]`, `direction: "Extract API URL from log; fix typo in path"` |
| **Safe code-transform strategy** | 1) Extract URL from log: `/api\/([a-zA-Z0-9_-]+)\/?`; 2) Check common typos: `availabilty`→`availability`, `availablity`→`availability`, `appointments` vs `appointment`; 3) Apply string replace only if single occurrence and path is in tests/. Guardrail: no backend URL changes |
| **Validation rules** | Rerun availability spec; response must be 200 |

---

### FS-4: api-404 (non-BROKEN)

| Field | Specification |
|-------|---------------|
| **Classification** | `api-404` |
| **Detection signals** | `404`, `Not Found`, `Failed to fetch`, `/api/` in request URL |
| **Fix-agent instructions** | Same as FS-3; add `key_log_snippets` with request URL |
| **Safe code-transform strategy** | 1) Extract requested path from log (e.g. `GET /api/availabilty/`); 2) Match against known routes: `availability`, `appointments`, `patients`, `doctors`; 3) Apply Levenshtein-like correction for 1-2 char typos. Guardrail: only fix if confidence > 0.9 (exact known route match) |
| **Validation rules** | Rerun API spec; 404 must resolve |

---

### FS-5: unknown (fallback)

| Field | Specification |
|-------|---------------|
| **Classification** | `unknown` |
| **Detection signals** | No match from other patterns |
| **Fix-agent instructions** | `suspected_paths: [tests/e2e/, tests/pages/]`, `direction: "Manual review required; first failing test and log snippet attached"` |
| **Safe code-transform strategy** | **No automatic transform.** Emit metadata with: `needs_manual_review: true`, `hints: { first_failing_test, log_snippet, suggested_paths }`. Produce empty patch. |
| **Validation rules** | N/A — no patch |

---

## Error Types That Cannot Be Repaired Automatically

### infra/network

| Reason | Explanation |
|--------|-------------|
| **No code fix** | Network failures (ECONNREFUSED, net::ERR_, DNS) are environment/transient. Fix-Agent cannot safely change code — retries/backoff belong in test harness or infra, not in application code. Self-heal (reseed + rerun) is the correct response. |
| **Fix scenario** | Self-heal: reseed_db, rerun_e2e_subset |

---

### auth/session

| Reason | Explanation |
|--------|-------------|
| **No safe transform** | Auth failures (401, 403, redirect to login) require understanding: E2E user creation, storageState, CSRF, JWT. Automated code edits risk breaking auth flow. Self-heal (regenerate storage + reseed + rerun) addresses transient session issues. |
| **Fix scenario** | Self-heal: regenerate_storage_state, reseed_db, rerun_e2e_subset |

---

### backend-migration

| Reason | Explanation |
|--------|-------------|
| **Requires schema analysis** | Migration failures need human analysis of migration order, dependencies, and schema conflicts. Automated edits could corrupt DB state. |
| **Fix scenario** | None — manual fix only. Fix-Agent outputs hints (migration output, backend.log snippet). |

---

### backend-exception

| Reason | Explanation |
|--------|-------------|
| **Requires traceback analysis** | Python tracebacks need mapping to code paths and root cause. Automated patching of backend code is high-risk without understanding. |
| **Fix scenario** | None — manual fix only. Fix-Agent outputs hints (traceback, suspected paths). |

---

### backend-500

| Reason | Explanation |
|--------|-------------|
| **Requires root cause analysis** | 500 errors can stem from many causes. Automated backend edits are unsafe. |
| **Fix scenario** | None — manual fix only. |

---

### missing_logs

| Reason | Explanation |
|--------|-------------|
| **No input** | Without logs, classification is impossible. No fix scenario can be generated. |
| **Fix scenario** | None — ensure logs are uploaded; retry workflow. |

---

## Summary: Fix Completeness by Error Type

| Error Type | Fix Exists | Complete | Partial | Missing | Auto-Repairable |
|------------|------------|----------|---------|---------|-----------------|
| frontend-selector (strict) | ✅ | ✅ | — | — | ✅ |
| frontend-selector (non-strict) | ❌ | — | — | ✅ | ⚠️ FS-1 (implementable) |
| frontend-timing (transient) | ✅ | — | ✅ | — | ✅ |
| frontend-timing (deterministic) | ✅ | — | ✅ | — | ⚠️ FS-2 (implementable) |
| frontend-availability (BROKEN) | ✅ | ✅ | — | — | ✅ |
| frontend-availability (non-BROKEN) | ❌ | — | — | ✅ | ⚠️ FS-3 (implementable) |
| api-404 (BROKEN) | ✅ | ✅ | — | — | ✅ |
| api-404 (non-BROKEN) | ❌ | — | — | ✅ | ⚠️ FS-4 (implementable) |
| infra/network | Self-heal | — | — | Code fix N/A | ❌ (by design) |
| auth/session | Self-heal | — | — | Code fix N/A | ❌ (by design) |
| backend-migration | ❌ | — | — | ✅ | ❌ |
| backend-exception | ❌ | — | — | ✅ | ❌ |
| backend-500 | ❌ | — | — | ✅ | ❌ |
| unknown | ❌ | — | — | ✅ | ⚠️ FS-5 (hints only) |
| missing_logs | ❌ | — | — | ✅ | ❌ |

---

## Implementation Checklist for New Fix Scenarios

| ID | Scenario | Implementation Tasks |
|----|----------|---------------------|
| FS-1 | frontend-selector (non-strict) | Add `extractNonStrictSelectors(playwrightLog)`; extend `addFirstForStrictLocator` to accept extracted selectors; add regex for "waiting for selector" / "Locator resolved to 0" |
| FS-2 | frontend-timing (deterministic) | Add `removeExcessiveWaitForTimeout(source)`; detect `waitForTimeout(60000)` or similar; replace with 500ms or remove |
| FS-3 | frontend-availability (non-BROKEN) | Extend `extractWrongApiUrl` to match `/api/([a-zA-Z0-9_-]+)/?`; add typo map (availabilty→availability); apply fix when single match |
| FS-4 | api-404 (non-BROKEN) | Reuse FS-3 logic; add known-route whitelist; apply only for high-confidence typo |
| FS-5 | unknown | Ensure `needs_manual_review: true` and hints in metadata; no code transform |

---

**End of Fix Scenario Specification**
