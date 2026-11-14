---
description: "Dependency-ordered implementation tasks for Personalized Shopping Copilot"
---

# Tasks: دستیار شخصی خرید

**Input**: artifacts in `/specs/002-personalized-shopping-copilot/`  
**Authorization**: Phase 7 planning only; every implementation task below remains pending.  
**TDD**: behavioral tests MUST fail for the intended missing behavior before paired implementation.

## Milestone A — Conversation foundation

- [ ] T001 [A] Revalidate exact existing dependency/runtime versions and record only necessary additions in `docs/tooling.md`; do not add a queue, WebSocket framework or provider framework
- [ ] T002 [P] [US1] Write failing model/constraint tests for Conversation, Message, ShoppingBrief, StreamOperation and StreamEvent in `backend/tests/integration/test_copilot_models.py`
- [ ] T003 [US1] Add reviewed migrations and models for T002 in `backend/analysis/models.py` and `backend/analysis/migrations/`; preserve feature 001 rows
- [ ] T004 [P] [US1] Write failing owner/CSRF/lifecycle/foreign-ID API tests in `backend/tests/api/test_conversations.py`
- [ ] T005 [US1] Implement owner-scoped conversation CRUD and brief revision CAS in `backend/analysis/api/conversations.py` and `backend/analysis/conversation/`
- [ ] T006 [P] [US1] Write failing pure brief-builder cases for self/gift/household, Persian money, unknowns, contradictions and image attribution in `backend/tests/unit/test_brief_builder.py`
- [ ] T007 [US1] Implement versioned brief normalization/confirmation without product-fact invention in `backend/analysis/conversation/brief.py`
- [ ] T008 [P] [US4] Write failing SSE contract tests for sequence, duplicate, reconnect gap, provisional/final, heartbeat and terminal errors in `backend/tests/api/test_stream_events.py`
- [ ] T009 [US4] Implement PostgreSQL-backed operation/event publication and same-origin SSE endpoint in `backend/analysis/conversation/streaming.py` and `backend/analysis/api/operations.py`
- [ ] T010 [US4] Write failing cancellation races for delete/cancel/brief-edit versus late publish in `backend/tests/integration/test_copilot_concurrency.py`, then implement operation-token guards outside network locks in `backend/analysis/conversation/operations.py`
- [ ] T011 [P] [US1] Write failing React component tests for Persian conversation, brief ribbon, upload validation, stop/error and bidi in `frontend/src/features/copilot/conversation/*.test.tsx`
- [ ] T012 [US1] Implement fixture-only conversation shell and API client in `frontend/src/features/copilot/conversation/` without changing default feature 001 route
- [ ] T049 [US1] Write failing upload API tests for owner isolation, CSRF, MIME/signature, size/count, metadata stripping, retention and delete races in `backend/tests/api/test_copilot_uploads.py`, then implement the bounded backend upload boundary in `backend/analysis/api/uploads.py` without object-storage dependency

**Checkpoint A**: fixture conversation/brief/stream works independently; no provider or research network.

## Milestone B — Evidence foundation

- [ ] T013 [B] Complete domain terms/robots review and approve an initial allowlist in `specs/002-personalized-shopping-copilot/source-feasibility.md`; unavailable domains stay disabled
- [ ] T014 [P] [US2] Write failing SourcePolicy/ResearchJob/Snapshot/Product/Variant/Offer/Claim constraints and migration tests in `backend/tests/integration/test_research_models.py`
- [ ] T015 [US2] Implement relational evidence entities and non-destructive migrations in `backend/analysis/models.py` and `backend/analysis/migrations/`
- [ ] T016 [P] [US2] Write failing URL/SSRF/redirect/private-address/DNS-rebinding/content-type/size/time/concurrency tests in `backend/tests/unit/test_safe_fetch.py`
- [ ] T017 [US2] Implement bounded allowlist fetch transport in `backend/analysis/research/fetch.py`; no browser/CAPTCHA/auth bypass
- [ ] T018 [P] [US2] Capture copyright-safe minimal fixtures for one approved source in each ready category and checksums in `backend/tests/fixtures/research/`; do not claim sports ready until direct extraction succeeds
- [ ] T019 [P] [US2] Write failing extractor/field-provenance/freshness tests for electronics, appliance and approved sports fixture in `backend/tests/unit/test_extractors.py`
- [ ] T020 [US2] Implement deterministic per-source extractors and schema validation in `backend/analysis/research/extractors/`
- [ ] T021 [P] [US2] Write failing variant reconciliation tests for region, identifier, bundle, warranty and ambiguity in `backend/tests/unit/test_variant_identity.py`
- [ ] T022 [US2] Implement identity/conflict handling and timed offer observations in `backend/analysis/research/identity.py`
- [ ] T023 [US2] Write failing bounded-job progress/cancel/cache/dedupe/failure integration tests in `backend/tests/integration/test_research_jobs.py`, then implement coordinator in `backend/analysis/research/jobs.py`

**Checkpoint B**: only approved fixture domains yield citations; access failures remain explicit.

## Milestone C — Choice Desk

- [ ] T024 [P] [US3] Write hand-authored ranking cases for budget, total cost, hard constraints, missing evidence, stale offer, gift context and ties in `backend/tests/unit/test_copilot_ranking.py`
- [ ] T025 [P] [US3] Write property/exhaustive invariants for determinism, no unsupported contribution and stable ties in `backend/tests/unit/test_ranking_invariants.py`
- [ ] T026 [US3] Implement `COPILOT-RANK-v0.1` pure pipeline in `backend/analysis/ranking/` and persist versioned ChoiceSet results
- [ ] T027 [P] [US3] Write API contract tests for ChoiceSet attribution, citations, coverage and unknown total-cost components in `backend/tests/api/test_choice_desk.py`
- [ ] T028 [US3] Implement current Choice Desk serializer/API in `backend/analysis/api/choices.py`
- [ ] T029 [P] [US3] Write React tests for cards/table/mobile disclosure, source drawer, long Persian/bidi, partial/final and keyboard semantics in `frontend/src/features/copilot/choice-desk/*.test.tsx`
- [ ] T030 [US3] Implement Choice Desk Concept 2 in `frontend/src/features/copilot/choice-desk/` using installed design skill plus project RTL/accessibility overlay and no new UI framework
- [ ] T031 [US3] Add Playwright journeys for 390/1440 viewports, keyboard, 200% zoom, stream stop and axe serious/critical zero in `tests/e2e/copilot-choice-desk.spec.ts`

**Checkpoint C**: fixture-based multi-category Choice Desk is deterministic and accessible; still no live provider.

## Milestone D — Opt-in memory and OpenAI readiness

- [ ] T032 [P] [US5] Write failing memory consent/candidate/confirmation/context/isolation/delete/export tests in `backend/tests/api/test_preference_memory.py`
- [ ] T033 [US5] Implement default-off preference memory and review/correct/delete APIs in `backend/analysis/memory/`
- [ ] T034 [D] Evaluate maintained encryption options against target-host key operations and record license/version/recovery decision in `docs/tooling.md` and `docs/decisions.md`; do not create custom crypto
- [ ] T035 [P] [US5] Write failing credential write-only, encryption, masking, rotation, deletion, log/redaction and missing-master-key tests in `backend/tests/unit/test_user_credentials.py`
- [ ] T036 [US5] Implement envelope-encrypted OpenAI credential storage with master key outside DB/image/Git in `backend/analysis/ai/credentials.py`
- [ ] T037 [P] [US4] Revalidate official model IDs/capabilities/pricing/data policy and freeze an allowlist/schema/cost policy in `specs/002-personalized-shopping-copilot/openai-readiness.md`
- [ ] T038 [P] [US4] Write stubbed Responses streaming adapter tests for structured output, image input, usage/request ID, timeout/retry/cancel/malformed/error in `backend/tests/unit/test_openai_copilot.py`
- [ ] T039 [US4] Implement direct OpenAI-only adapter behind existing seam in `backend/analysis/ai/openai_copilot.py`; `store=false`, no AvalAI fallback and no live calls in unsupported region
- [ ] T040 [US5] Write factory/settings tests proving offline default, missing configuration fail-closed, Iran eligibility blocked despite key and operation/session cost cap in `backend/tests/test_copilot_configuration.py`, then wire non-secret settings
- [ ] T041 [P] [US5] Add masked key/memory controls and billing-vs-ChatGPT copy tests/UI in `frontend/src/features/copilot/memory/`

**Checkpoint D**: stubbed integration only. Live OpenAI remains blocked until official region eligibility and separate spending authorization.

## Milestone E — Operations rehearsal and controlled pilot gates

- [ ] T042 [E] Finalize and approve per-entity retention, export/deletion and backup-erasure caveat in `docs/decisions.md` and operations docs
- [ ] T043 [P] [US4] Add NGINX/Django SSE buffering, timeout, disconnect and graceful-shutdown configuration tests before editing `deploy/web.conf` or production Compose
- [ ] T044 [E] Rehearse one-command offline Compose with conversation/research fixture/Choice Desk, container recreation, PostgreSQL persistence, backup/restore and no provider key/call
- [ ] T045 [E] Run browser smoke only for implemented copilot route and verify target-host Host/CSRF/proxy/stream behavior; do not public deploy
- [ ] T046 [E] Run source allowlist review, privacy threat model, cost cap review and OpenAI official region check; record each as independent go/no-go
- [ ] T047 [E] Execute controlled live evaluation only after explicit eligibility and spending authorization; otherwise record zero calls and exact blocker
- [ ] T048 [E] Prepare cutover/rollback evidence per `migration-coexistence.md`; product lead must separately approve default-route change and legacy retirement
- [ ] T050 [E] Write failing owner-scoped export tests and implement a minimal JSON export for conversation, current brief, citations and confirmed memory in `backend/tests/api/test_copilot_export.py` and `backend/analysis/api/export.py`; exclude credential ciphertext/plaintext, raw cache and private operational metadata

## Dependencies

`A → B → C`; memory work in D depends on A, adapter work depends on A streaming, and E depends on selected completed milestones. T049 follows T003/T005 and blocks image use. T013 blocks live source access. T034 blocks credential implementation. T037/T040 and official region support block any live call. T050 follows A/D data ownership. T047 never completes merely from a key. Feature 001 `T039` remains independent and pending.

## Implementation strategy

Implement only a separately authorized milestone. Stop at each checkpoint and use offline fixtures first. No task here is complete in Phase 7; planning artifacts are not executable evidence.
