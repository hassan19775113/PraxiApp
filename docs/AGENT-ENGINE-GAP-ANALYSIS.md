# Agent-Engine: Test Scenarios vs Fix Scenarios Gap Analysis

**Date:** 2026-02-15  
**Scope:** E2E test scenarios (`tests/e2e/`), classification types, fix paths, self-heal, Fix-Agent

---

## E2E Test Scenarios vs Fix Paths

| E2E Spec | Scenarios Covered | Possible Failure Modes | Fix Path | Gap |
|----------|-------------------|-------------------------|----------|-----|
| **appointment-modal.spec.ts** | Calendar edit, modal, availability | selector, timeout, auth | ✅ selector/timeout/availability | timeout fix masks root cause |
| **calendar.spec.ts** | Create appointment, availability | selector, auth, availability API | ✅ | — |
| **appointments-availability-doctors.spec.ts** | Availability modal, doctors dropdown | selector, auth, availability API | ✅ | — |
| **appointments-conflicts.spec.ts** | Conflict UI, availability | selector, auth, availability API | ✅ | — |
| **appointments-patient-conflicts.spec.ts** | Patient conflict, availability | selector, auth, availability API | ✅ | — |
| **appointments-doctor-conflicts.spec.ts** | Doctor conflict, availability | selector, auth, availability API | ✅ | — |
| **appointments-boundary-overlaps.spec.ts** | Boundary overlap, availability | selector, auth, availability API | ✅ | — |
| **appointments-conflicts-mega.spec.ts** | Multi-conflict, availability | selector, auth, availability API | ✅ | — |
| **appointments-new-termin-dropdowns.spec.ts** | New appointment dropdowns | selector, auth | ⚠️ | auth: no code fix |
| **appointments-visibility.spec.ts** | Card visibility | selector, auth | ⚠️ | auth: no code fix |
| **appointments-session-fallback.spec.ts** | Session auth fallback | auth/session | ❌ | auth: no code fix |
| **patients-smoke.spec.ts** | Patients list | selector (#patientsTable), auth | ⚠️ | auth: no code fix; selector non-strict |
| **operations-smoke.spec.ts** | Operations dashboard | selector (#periodSelect), auth | ⚠️ | auth: no code fix; selector non-strict |
| **operations.spec.ts** | Operations charts | selector, auth | ⚠️ | auth: no code fix |
| **patients.spec.ts** | Patients UI | selector, auth | ⚠️ | auth: no code fix |
| **patients-crud.spec.ts** | Patients CRUD | selector, auth | ⚠️ | auth: no code fix |
| **doctors-crud.spec.ts** | Doctors CRUD | selector, auth | ⚠️ | auth: no code fix |
| **resources-crud.spec.ts** | Resources CRUD | selector, auth, 403 | ⚠️ | auth: no code fix |
| **appointment-types-crud.spec.ts** | Appointment types CRUD | selector, auth, 403 | ⚠️ | auth: no code fix |
| **navigation.spec.ts** | Header navigation | selector ([role="navigation"]), auth | ⚠️ | auth: no code fix |
| **appointments-visibility.spec.ts** | Card visibility | selector, auth | ⚠️ | auth: no code fix |
| **appointments-session-fallback.spec.ts** | Session auth fallback | auth/session | ❌ | auth: no code fix |
| **api.spec.ts** | Appointments, availability, doctors, types | network, auth, 404 | ❌ | network/auth: no code fix |
| **availability-correctness.spec.ts** | API availability logic | network, backend | ❌ | no code fix |
| **roles.spec.ts** | Role-based auth | auth, 403 | ❌ | auth: no code fix |
| **scheduling-kpis.spec.ts** | Scheduling KPIs | auth | ⚠️ | auth: no code fix |
| **sanity-fail.spec.ts** | Intentional failure (disabled) | — | — | N/A |

### Controlled Fault Injection (FAULT_SCENARIO)

| Scenario | File | Line | Injection | Fix Path |
|----------|------|------|-----------|----------|
| **selector** | `tests/pages/calendar-page.ts` | 26 | `#appointmentCalendarBROKEN` | ✅ addFirstForStrictLocator (partial) |
| **timeout** | `tests/e2e/appointment-modal.spec.ts` | 18 | `waitForTimeout(60_000)` | ✅ test.setTimeout(60s) |
| **availability** | `tests/pages/appointment-modal-page.ts` | 163 | `/api/availabilityBROKEN/?` | ✅ fixWrongApiUrlInSource |

### CI Smoke Tests (Run Before Full E2E)

| Job | Spec | Failure Modes | Fix Path |
|-----|------|---------------|----------|
| patients-ui-smoke | patients-smoke.spec.ts | auth, selector | auth: self-heal only |
| operations-ui-smoke | operations-smoke.spec.ts | auth, selector | auth: self-heal only |
| availability-ui-smoke | appointments-availability-doctors.spec.ts | auth, selector, availability | ✅ |

---

## Summary Matrix

| Error Type | Detected | Self-Heal | Fix-Agent Auto-Patch | Fix Complete | Fix Safe | Cannot Repair |
|------------|----------|-----------|----------------------|--------------|----------|---------------|
| **frontend-selector** | ✅ | ❌ Denied | ✅ `.first()` for strict-mode | ⚠️ Partial | ✅ | Non–strict-mode selector faults |
| **frontend-timing** | ✅ | ✅ When transient | ✅ `test.setTimeout(60s)` | ⚠️ Partial | ⚠️ | Deterministic timing (masks root cause) |
| **frontend-availability** | ✅ | ❌ Denied | ✅ URL typo (`*BROKEN`→correct) | ⚠️ Partial | ✅ | Non-BROKEN URL errors |
| **api-404** | ✅ | ❌ Denied | ✅ URL typo (`*BROKEN`→correct) | ⚠️ Partial | ✅ | Non-BROKEN 404s |
| **infra/network** | ✅ | ✅ When transient | ❌ No transform | ❌ | N/A | **Yes** |
| **auth/session** | ✅ | ✅ When transient | ❌ No transform | ❌ | N/A | **Yes** |
| **backend-migration** | ✅ | ❌ Denied | ❌ No transform | ❌ | N/A | **Yes** |
| **backend-exception** | ✅ | ❌ Denied | ❌ No transform | ❌ | N/A | **Yes** |
| **backend-500** | ✅ | ❌ Denied | ❌ No transform | ❌ | N/A | **Yes** |
| **unknown** | ✅ | ❌ Denied | ❌ No transform | ❌ | N/A | **Yes** |
| **missing_logs** | ✅ | ❌ Denied | ❌ No transform | ❌ | N/A | **Yes** |

---

## Per-Scenario Analysis

### 1. frontend-selector

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ✅ Yes |
| **Fix complete** | ⚠️ Partial — only strict-mode violations (`locator('...') resolved to N elements`) |
| **Fix safe** | ✅ Yes — `.first()` is low-risk |
| **Missing/unhandled** | Non–strict-mode selector faults (e.g. "waiting for selector", "element not found") produce no patch. `extractStrictModeSelectors` requires strict-mode message in logs. |
| **Cannot repair** | Wrong selector, missing element, non-strict locator failures |

---

### 2. frontend-timing

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ✅ Yes |
| **Fix complete** | ⚠️ Partial — adds `test.setTimeout(60000)` only |
| **Fix safe** | ⚠️ — Can mask real timeout causes; may hide flaky waits |
| **Missing/unhandled** | No change to wait logic. Deterministic timing failures (e.g. 60s sleep) still fail after rerun. Self-heal skipped when deterministic (transience=low). |
| **Cannot repair** | Deterministic timing failures; root cause is not addressed |

---

### 3. frontend-availability

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ✅ Yes |
| **Fix complete** | ⚠️ Partial — only `*BROKEN` suffix in URL |
| **Fix safe** | ✅ Yes — simple string replacement |
| **Missing/unhandled** | `extractWrongApiUrl` only matches `/api/([a-zA-Z0-9_-]+BROKEN)`. Wrong path, wrong segment, or other typos are not fixed. |
| **Cannot repair** | Wrong path, wrong segment, non-BROKEN availability URL errors |

---

### 4. api-404

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ✅ Yes |
| **Fix complete** | ⚠️ Partial — same as frontend-availability |
| **Fix safe** | ✅ Yes |
| **Missing/unhandled** | Same as frontend-availability. Generic 404s (e.g. wrong route, missing backend) are not auto-fixed. |
| **Cannot repair** | Wrong route, missing backend route, non-BROKEN URL |

---

### 5. infra/network

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ✅ Self-heal only (reseed + rerun) |
| **Fix complete** | ❌ No code fix |
| **Fix safe** | ✅ Self-heal is safe (no code edits) |
| **Missing/unhandled** | Fix-Agent has instructions but no automatic transform. Guardrail: "do not attempt backend changes without explicit, localized targets." Produces empty patch. |
| **Cannot repair** | **Yes** — No code fix. Self-heal may help transient failures. |

---

### 6. auth/session

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ✅ Self-heal only (regenerate storage + reseed + rerun) |
| **Fix complete** | ❌ No code fix |
| **Fix safe** | ✅ Self-heal is safe |
| **Missing/unhandled** | Fix-Agent has instructions (suspected_paths: django/, backend/) but no transform. `isAllowedPath` allows django/ but no auth-specific transform exists. |
| **Cannot repair** | **Yes** — No automatic code fix. |

---

### 7. backend-migration

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ❌ No |
| **Fix complete** | ❌ No |
| **Fix safe** | N/A |
| **Missing/unhandled** | Fix-Agent has instructions but no transform. Migration/schema fixes require human intervention. |
| **Cannot repair** | **Yes** |

---

### 8. backend-exception

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ❌ No |
| **Fix complete** | ❌ No |
| **Fix safe** | N/A |
| **Missing/unhandled** | Fix-Agent has instructions (suspected_paths: django/) but no transform. Traceback requires code analysis. |
| **Cannot repair** | **Yes** |

---

### 9. backend-500

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ❌ No |
| **Fix complete** | ❌ No |
| **Fix safe** | N/A |
| **Missing/unhandled** | Same as backend-exception. |
| **Cannot repair** | **Yes** |

---

### 10. unknown / missing_logs

| Aspect | Status |
|--------|--------|
| **Fix path exists** | ❌ No |
| **Fix complete** | ❌ No |
| **Fix safe** | N/A |
| **Missing/unhandled** | No classification → no fix_agent_instructions → empty patch, needs_manual_review. |
| **Cannot repair** | **Yes** |

---

## Missing Mappings (High-Level)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DETECTED (Classification)          →    FIX PATH (Automatic)               │
├─────────────────────────────────────────────────────────────────────────────┤
│  frontend-selector (strict-mode)    →    ✅ addFirstForStrictLocator        │
│  frontend-selector (other)          →    ❌ MISSING                         │
│  frontend-timing                    →    ✅ addFileLevelTimeoutIfMissing    │
│  frontend-availability (*BROKEN)    →    ✅ fixWrongApiUrlInSource          │
│  frontend-availability (other)      →    ❌ MISSING                         │
│  api-404 (*BROKEN)                  →    ✅ fixWrongApiUrlInSource          │
│  api-404 (other)                    →    ❌ MISSING                         │
│  infra/network                     →    ❌ NO CODE FIX (self-heal only)     │
│  auth/session                      →    ❌ NO CODE FIX (self-heal only)     │
│  backend-migration                 →    ❌ NO CODE FIX                      │
│  backend-exception                 →    ❌ NO CODE FIX                      │
│  backend-500                       →    ❌ NO CODE FIX                      │
│  unknown / missing_logs             →    ❌ NO CODE FIX                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Error Types That Cannot Be Repaired Automatically

| Error Type | Reason |
|------------|--------|
| **infra/network** | No code transform; self-heal only (reseed + rerun) |
| **auth/session** | No code transform; self-heal only |
| **backend-migration** | Schema/migration changes require human analysis |
| **backend-exception** | Traceback requires code analysis and targeted fix |
| **backend-500** | Server error requires root cause analysis |
| **unknown** | No classification → no instructions |
| **missing_logs** | No classification → no instructions |
| **frontend-selector** (non-strict) | No strict-mode message → no patch |
| **frontend-availability** (non-BROKEN) | No URL pattern match |
| **api-404** (non-BROKEN) | No URL pattern match |

---

## Recommendations

1. **frontend-selector:** Add fallback for "waiting for selector" / "element not found" — e.g. extract selector from log and suggest `data-testid` or `role` locator (requires heuristics).
2. **frontend-availability / api-404:** Broaden `extractWrongApiUrl` to handle more URL patterns (e.g. wrong path segments, common typos).
3. **backend-* / auth:** Document that these require manual fix; consider adding "Fix-Agent hints" output (suspected paths, direction) for human use.
4. **infra/network:** Keep self-heal as primary path; no code fix is appropriate for transient network issues.
5. **unknown:** Improve classification patterns to reduce fallback to `unknown`; add more log signals.

---

## E2E Test Scenarios vs Fix Scenarios: Concise Mapping

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  E2E TEST SCENARIO (tests/e2e/)              →  FAILURE MODE    →  FIX PATH              │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  Calendar + modal (selector fault)            →  frontend-selector →  ✅ Partial (.first)  │
│  Appointment modal (timeout fault)           →  frontend-timing   →  ✅ Partial (setTimeout)│
│  Availability API (availability fault)       →  frontend-availability →  ✅ Partial (BROKEN)│
│  Any spec: redirect to /admin/login          →  auth/session      →  ❌ Self-heal only   │
│  Any spec: 401/403 in API                    →  auth/session      →  ❌ Self-heal only   │
│  API spec: ECONNREFUSED, net::ERR_           →  infra/network      →  ❌ Self-heal only   │
│  API spec: 404 on /api/...                   →  api-404           →  ✅ Partial (BROKEN) │
│  Backend traceback in logs                   →  backend-exception  →  ❌ No fix           │
│  Backend 500 in logs                         →  backend-500       →  ❌ No fix           │
│  Migration failed                            →  backend-migration  →  ❌ No fix           │
│  Patients/operations smoke: #patientsTable   →  frontend-selector →  ⚠️ Non-strict: no fix│
│  Unmatched log pattern                       →  unknown            →  ❌ No fix           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### E2E Specs With No Automatic Fix

| Spec | Failure Mode | Reason |
|------|--------------|--------|
| api.spec.ts | network, auth | No code transform for infra/auth |
| availability-correctness.spec.ts | backend | API logic; no Fix-Agent transform |
| roles.spec.ts | auth/403 | No code fix |
| appointments-session-fallback.spec.ts | auth/session | Self-heal only |

### E2E Specs With Partial Fix

| Spec | Failure Mode | Fix | Gap |
|------|--------------|-----|-----|
| appointment-modal.spec.ts | selector, timeout, availability | ✅ | timeout masks root cause |
| calendar.spec.ts | availability | ✅ | — |
| appointments-*-conflicts*.spec.ts | availability | ✅ | — |
| appointments-availability-doctors.spec.ts | availability | ✅ | — |
| patients-smoke.spec.ts | selector | ⚠️ | Non-strict selector (e.g. #patientsTable) not fixed |
| operations-smoke.spec.ts | selector | ⚠️ | Non-strict selector (#periodSelect) not fixed |

---

## Related: Fix Scenario Specification

For concrete fix scenarios (classification, detection signals, fix-agent instructions, safe code-transform strategy, validation rules) for every error type — including newly generated specs for missing/partial cases — see **`docs/FIX-SCENARIO-SPECIFICATION.md`**.

---

**End of Gap Analysis**
