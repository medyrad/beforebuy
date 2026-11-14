---
description: "Dependency-ordered implementation tasks for Purchase Decision Analysis"
---

# Tasks: تحلیل تصمیم خرید تلفن همراه

**Input**: `spec.md`, `plan.md`, `data-model.md`, `contracts/openapi.yaml`, `research.md`, `quickstart.md`  
**Milestone authorization**: M1/M2 are accepted. Phase 5.2 may complete only the Iran-provider **M3 adaptation** IDs
`T049`–`T052`; `T039` remains open until real live/human evidence and M4 remains unchecked/unimplemented.  
**TDD**: Every behavioral test task runs red before its paired implementation task; PostgreSQL is mandatory for race claims.

## Phase 1: Setup and reproducibility — M1

**Purpose**: Project-local backend tooling and a reproducible Django/PostgreSQL development surface.

- [x] T001 **[M1]** Validate and register the focused backend skill at `.agents/skills/django-drf-backend/SKILL.md` and record its version/source in `docs/tooling.md`
- [x] T002 **[M1]** Create project-scoped Python metadata and exact lockfile for supported Django 5.2 LTS, DRF, psycopg and test/runtime dependencies in `pyproject.toml` and `uv.lock`
- [x] T003 **[M1]** Create the minimal Django modular-monolith scaffold and environment-separated settings in `backend/manage.py`, `backend/config/settings/`, `backend/config/urls.py`, `backend/config/wsgi.py`, and `backend/analysis/`
- [x] T004 **[M1]** Add development-only PostgreSQL/API services, health checks and persistent volume in `compose.yaml`, `deploy/api.Dockerfile`, `.env.example`, and `.dockerignore`; do not add the production web service
- [x] T005 **[M1]** Add startup/configuration smoke tests for database settings, safe logging and installed middleware in `backend/tests/test_configuration.py`, verify red, then complete settings in `backend/config/settings/`

**Checkpoint**: Locked dependencies install; Django starts against the development PostgreSQL service.

---

## Phase 2: Foundational ownership, persistence and safety — M1

**Purpose**: Blocks all user stories. Covers `FR-024..FR-031`, `AC-HIS-001..011` and the corrected Phase 3 concurrency model.

- [x] T006 **[M1]** Write failing model/constraint tests for `GuestContext`, `Analysis`, `CurrentReport` and `UsefulnessFeedback`—including product label max 120, price `>0`, budget null-or-`>=0`, revisions positive and rating `1..5`—in `backend/tests/integration/test_models.py`
- [x] T007 **[M1]** Implement those entities and indexes, including `access_expires_at`, `generation_epoch` and `report_operation_token`, in `backend/analysis/models.py` and create `backend/analysis/migrations/0001_initial.py`
- [x] T008 **[M1]** Write failing guest bootstrap/session lifetime tests for day-0 bootstrap, day-89 new analysis extension to day 179, no extension on read/edit/retry/feedback, and cookie-loss limitation in `backend/tests/api/test_guest_session.py`
- [x] T009 **[M1]** Implement opaque database-session guest ownership and new-analysis-only lifetime extension in `backend/analysis/guest.py` and `backend/analysis/api/session.py`
- [x] T010 **[M1]** Write failing CSRF/Host/Origin API tests with enforcement enabled for missing token, invalid token, valid same-origin flow and rejected untrusted host/origin in `backend/tests/api/test_csrf.py`
- [x] T011 **[M1]** Implement `ensure_csrf_cookie` bootstrap and a `csrf_protect` DRF base for every unsafe endpoint in `backend/analysis/api/base.py`, `backend/analysis/api/session.py`, and `backend/config/settings/`
- [x] T012 **[M1]** Write failing transaction tests with controlled barriers for clear-history versus initial create, delete during retry and competing retries on one input revision in `backend/tests/integration/test_concurrency.py`
- [x] T013 **[M1]** Implement short-transaction publication, guest epoch clear barrier and per-analysis operation-token compare-and-swap in `backend/analysis/services.py`; keep generator/network work outside transactions
- [x] T014 **[M1]** Write failing cleanup tests for immediate expiry denial, expired analysis cascade, unused guest cleanup and expired Django sessions in `backend/tests/integration/test_cleanup.py`
- [x] T015 **[M1]** Implement `purge_expired_analyses` and session cleanup in `backend/analysis/management/commands/purge_expired_analyses.py` and document cron/systemd scheduling in `docs/backend-operations.md`

**Checkpoint**: PostgreSQL migrations and concurrency/lifecycle invariants pass independently of report behavior.

---

## Phase 3: User Story 1 — evidence-grounded decision report (Priority P1) — M1 backend / M2 UI

**Goal**: A guest submits the bounded phone questionnaire and receives one deterministic, scoped report.  
**Independent Test**: `SYN-001..010`, `AC-VAL-001..004`, `AC-RUB-001..008`, `AC-EVD-001..002`, and `AC-AI-001..004` pass through the create/read API without target-product overclaim.

### Tests first — M1

- [x] T016 [P] [US1] **[M1]** Write failing literal money-normalization tests for Persian/Latin digits, valid grouping, malformed/decimal/scientific/currency input, positive price, zero budget and explicit unknown in `backend/tests/unit/test_money.py`
- [x] T017 [P] [US1] **[M1]** Write failing hand-authored rubric tests for `SYN-001..009`, explicit precedence mutations and independent dimensions in `backend/tests/unit/test_engine_scenarios.py`
- [x] T018 [P] [US1] **[M1]** Write failing exhaustive invariants for all 1,134 categorical combinations—exactly one dimension status/outcome and ordered totality—as a supplemental oracle in `backend/tests/unit/test_engine_invariants.py`
- [x] T019 [P] [US1] **[M1]** Write failing explanation-contract tests for mock labeling, allowed claim templates, evidence ID plus type/content compatibility, malformed/unsupported/contradictory output and limited fallback in `backend/tests/unit/test_explanation.py`
- [x] T020 [US1] **[M1]** Write failing create/read/list contract tests for validation envelope, owner isolation, expiry filtering, `MOCK_ASSISTED` metadata and OpenAPI examples in `backend/tests/api/test_analysis_create_read.py`

### Implementation — M1

- [x] T021 [US1] **[M1]** Implement pure whole-toman normalization and validation in `backend/analysis/domain/money.py` to satisfy T016 and `VAL-01..02`
- [x] T022 [US1] **[M1]** Implement immutable domain types and authoritative `PDA-CAT-v0.3` dimension/outcome engine in `backend/analysis/domain/types.py`, `backend/analysis/domain/rules.py`, and `backend/analysis/domain/engine.py` to satisfy T017–T018
- [x] T023 [US1] **[M1]** Implement `ExplanationGenerator`, explicit `MockExplanationGenerator`, typed claim validator and rule-based fallback in `backend/analysis/ai/contracts.py`, `backend/analysis/ai/generator.py`, and `backend/analysis/ai/validator.py` to satisfy T019; never emit `AI_ASSISTED_SUCCESS` from mock
- [x] T024 [US1] **[M1]** Implement serializers and consistent error envelope for the schema-versioned eight fields plus at most three follow-ups in `backend/analysis/api/serializers.py` and `backend/analysis/api/errors.py`
- [x] T025 [US1] **[M1]** Implement guest-owned create/list/read endpoints and routes from OpenAPI in `backend/analysis/api/views.py` and `backend/analysis/api/urls.py`, using atomic first publication and no persistence on undisplayable failure

### Frontend — M2, authorized in Phase 4

- [x] T026 [P] [US1] **[M2]** Install/pin scoped React/Vite skills and create frontend lock/scaffold in `frontend/` without Next.js or Vercel deployment requirements
- [x] T027 [US1] **[M2]** Implement Persian/RTL questionnaire, validation, loading and independent report dimension components in `frontend/src/features/analysis/` with component accessibility tests in `frontend/tests/`

**Checkpoint**: US1 backend is independently testable after T025; Phase 4 integrates its M2 UI.

---

## Phase 4: User Story 2 — edit, retry and usefulness feedback (Priority P2) — M1 backend / M2 UI

**Goal**: A guest edits current inputs, retries report generation and manages one rating bound to current report content/mode.  
**Independent Test**: `SYN-011`, `AC-EDT-001..002`, and `AC-FBK-001..005` pass with stale operations unable to overwrite report or feedback.

- [x] T028 [P] [US2] **[M1]** Write failing API tests for edit recomputation, stale input/report revision 409, identical retry preservation, changed retry rating invalidation and feedback create/change/remove in `backend/tests/api/test_revision_feedback.py`
- [x] T029 [US2] **[M1]** Implement edit/reanalysis/feedback serializers, services and endpoints in `backend/analysis/api/serializers.py`, `backend/analysis/services.py`, and `backend/analysis/api/views.py` to satisfy T028 and operation-token rules
- [x] T030 [US2] **[M2]** Implement Persian edit/retry/rating UI states without carrying feedback across changed reports in `frontend/src/features/analysis/` and `frontend/tests/`

**Checkpoint**: US2 backend can be tested without UI or a live AI provider.

---

## Phase 5: User Story 3 — private same-browser history and deletion (Priority P3) — M1 backend / M2 UI

**Goal**: A guest lists, opens, deletes one analysis or atomically clears all history within the same browser.  
**Independent Test**: `SYN-012`, `AC-HIS-001..011` pass across two clients, expiry and controlled concurrency.

- [x] T031 [P] [US3] **[M1]** Write failing API tests for newest-first history, foreign/expired/deleted 404, delete-one cascade and clear-history response/error contract in `backend/tests/api/test_history.py`
- [x] T032 [US3] **[M1]** Implement delete and epoch-advancing clear-history endpoints in `backend/analysis/api/views.py`, `backend/analysis/services.py`, and `backend/analysis/api/urls.py` to satisfy T031 and T012
- [x] T033 [US3] **[M2]** Implement Persian empty/expired/deleted/history navigation and clear confirmation in `frontend/src/features/history/` with browser-independent component tests
- [x] T034 [US3] **[M2]** Add the small repeatable Playwright CLI journey set after its trigger evaluation in `tests/e2e/`; do not substitute MCP exploration for tests

**Checkpoint**: All three backend stories are complete at T032; Phase 4 implements their M2 surfaces.

---

## Phase 6: M1 verification and documentation

- [x] T035 **[M1]** Validate OpenAPI syntax/examples and implemented route/status/error parity in `specs/001-purchase-decision-analysis/contracts/openapi.yaml` and `backend/tests/api/test_openapi_contract.py`
- [x] T036 **[M1]** Run dependency install, Django checks, migration drift check, empty-PostgreSQL migration, full unit/API/integration suite and development Compose startup; record exact commands/results in `docs/handoff.md`
- [x] T037 **[M1]** Add a reproducible cookie/CSRF local smoke sequence and explicit mock-only limitations in `README.md`, `specs/001-purchase-decision-analysis/quickstart.md`, and `docs/backend-operations.md`

---

## Phase 7: Real AI readiness — M3

- [x] T038 **[M3]** Select and pin a real provider/model, timeout, bounded retries, token/cost ceiling and evaluation dataset in `docs/decisions.md` and `specs/001-purchase-decision-analysis/research.md`
- [ ] T039 [P] **[M3]** Write provider-contract and live evaluation tests that remain separate from mock tests in `backend/tests/ai/` — contract/harness tests pass؛ task remains open until an authorized real-provider run supplies live evidence
- [x] T040 **[M3]** Implement one real `ExplanationGenerator` adapter in `backend/analysis/ai/` and prove no deterministic result override; retain explicit limited fallback

### Phase 7.1: Verified M3 review corrections — Phase 5.1

- [x] T044 [P] **[M3]** Add failing claim/evaluation tests for value-aware target support, contradictory inputs,
  independent structural versus human criteria, semantic limits, Persian-digit fixtures and reproducible synthetic
  review artifacts in `backend/tests/ai/` and `backend/tests/unit/test_explanation.py`
- [x] T045 [P] **[M3]** Add failing cost-ledger tests for complete request reservation, concurrent windows, retry/unknown
  usage, observed overage and idempotent settlement in `backend/tests/ai/`; then implement one shared pricing/reservation
  module used by adapter and evaluation command without moving network calls into transactions
- [x] T046 **[M3]** Implement deterministic headline/reasons and value-aware typed claim validation in
  `backend/analysis/domain/`, `backend/analysis/ai/` and `backend/analysis/services.py`; document which semantic checks
  remain human-only and never present them as automatic
- [x] T047 **[M3]** Replace fabricated evaluation success with per-case operational evidence and a synthetic human-review
  artifact tied to run/model/prompt/schema in `backend/analysis/ai/evaluation.py`, management commands and
  `specs/001-purchase-decision-analysis/ai-evaluation.md`; keep `T039` open without a real run/review
- [x] T048 **[M3]** Improve only result copy, mobile dimension density and accessible feedback endpoints in the existing
  React/Vite UI; run focused/full regressions and refreshed desktop/mobile browser screenshots, then archive the Phase 5
  handoff and record Phase 5.1 evidence in `docs/handoff.md`

### Phase 7.2: Iran-appropriate provider adaptation — Phase 5.2

- [x] T049 **[M3]** Compare at most two Iran-serving hosted providers from current primary sources; record protocol,
  exact model, schema/usage/error behavior, tariff, credit/top-up, retention and unresolved upstream authorization in
  `research.md`, `docs/decisions.md` and `docs/tooling.md`; keep direct OpenAI disabled
- [x] T050 [P] **[M3]** Add failing AvalAI adapter/factory/evaluation tests for documented Responses schema, usage/request
  metadata, errors, fresh IRT conversion and a total 100,000-toman retry-inclusive cap in `backend/tests/ai/`
- [x] T051 **[M3]** Implement the single selected AvalAI `gpt-5.6-luna` Responses adapter through the existing
  `ExplanationGenerator`, provider-specific tariff/conversion gates, minimal invocation metadata migration and
  fail-closed factory without a provider registry
- [x] T052 **[M3]** Prepare the unchanged synthetic baseline-versus-AI artifact workflow, run affected/full regressions,
  execute a live run only if all eligibility/credential/credit gates are already satisfied, and update `docs/handoff.md`؛
  leave `T039` open until live evidence and human review both exist

---

## Phase 8: Production packaging and operations — M4

- [ ] T041 **[M4]** Add production static frontend gateway and hardened images in `deploy/web.Dockerfile`, `deploy/web.conf`, `deploy/api.Dockerfile`, and `compose.production.yaml`
- [ ] T042 [P] **[M4]** Define backup retention/erasure, migration and rollback responsibilities in `docs/backend-operations.md`
- [ ] T043 **[M4]** Execute and record health/readiness, migration, backup/restore and rollback rehearsals on a production-like PostgreSQL stack in `docs/handoff.md`

---

## Dependencies and execution order

```text
T001 → T002 → T003/T004 → T005
T005 → T006→T007, T008→T009, T010→T011, T012→T013, T014→T015
Foundation → T016/T017/T018/T019/T020 → T021/T022/T023/T024/T025
US1 backend → T028→T029 and T031→T032 → T035→T036→T037
M1 complete → M2 (T026/T027/T030/T033/T034)
M1 complete + explicit provider decisions → M3 (T038–T040) → review corrections (T044–T048) → Iran adaptation (T049–T052)
M1+M2+M3 readiness → M4 (T041–T043)
```

- Tests always precede their paired implementation and must fail for the missing behavior, not setup errors.
- `[P]` means different files/no incomplete dependency; this phase uses one agent and does not imply delegation.
- PostgreSQL concurrency tests T012 are blocking evidence for T013/T032 and cannot be replaced by SQLite.
- During Phase 5 only M3 tasks may change to complete; M4 remains unchecked and unimplemented. A task that requires
  live evidence remains unchecked when region، credential یا budget صریح فراهم نیست.

## Parallel examples

- **US1 after foundation**: T016 money, T017 scenarios, T018 invariants and T019 explanation contract touch separate
  test files and may be authored independently before their production tasks.
- **Later milestones**: frontend component work and real-provider evaluation are independent only after M1 contracts are
  stable; production packaging waits for all readiness decisions.

## Implementation strategy

1. Treat accepted M1/M2 as the integration baseline; do not recreate them.
2. Freeze provider/contract/evaluation decisions in T038, then execute T039/T040 with provider-boundary red-green cycles.
3. Keep live mode opt-in؛ verify PostgreSQL-backed budget/circuit state، deterministic authority و limited fallback.
4. Run live evaluation only with AvalAI eligibility، local credential/credit، fresh IRT rate و explicit cap at most
   100,000 toman; otherwise record zero calls/cost and leave the live-evidence task incomplete.
5. Complete verified Phase 5.1 corrections while leaving T039 open until real live/human evidence؛ M4 requires later authorization.
6. Phase 5.2 does not reactivate direct OpenAI, purchase credit, create an account, deploy or implement M4.
