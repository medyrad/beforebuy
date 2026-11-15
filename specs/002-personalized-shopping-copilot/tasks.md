---
description: "Dependency-ordered implementation tasks for Personalized Shopping Copilot"
---

# Tasks: دستیار شخصی خرید

## Phase 12 — provider-neutral real conversational path

- [x] T078 [D] Record product-lead supersession of OpenAI exclusivity; compare at most GapGPT/AvalAI from official sources and freeze selected/fallback evidence, tariff, protocol and unresolved gates.
- [x] T079 [P] [US5] Write failing migration/credential/API tests for explicit provider association, preserved OpenAI ciphertext, independent GapGPT credential lifecycle and zero-call save/read/settings.
- [x] T080 [US5] Add the minimal additive provider/settings/credential migration and backend APIs; no arbitrary base URL or credential reinterpretation.
- [x] T081 [P] [US4] Write failing GapGPT Chat Completions streaming adapter tests for fixed endpoint/model, bounded JSON plan, natural Persian acknowledgement/question, usage/missing-usage accounting, timeout/retry/cancel/error and unsupported facts.
- [x] T082 [US4] Implement the selected GapGPT adapter behind the existing context/worker/SSE/budget seam; retain OpenAI as region-blocked optional and preserve deterministic evidence publication.
- [x] T083 [P] [US5] Write failing React settings tests for provider discovery, separate credential states, no implicit validation/call and exact local configuration/help copy.
- [x] T084 [US5] Implement the Persian settings/provider UI and conversational copy without a technical-brief prerequisite or secret exposure.
- [x] T085 [US4] Run Spec Kit analyze, focused/full backend/frontend/browser verification, document the exact live credential/budget gate and synthetic evaluation scenarios, archive handoff, then commit/push related files only; keep T066, feature001 T039 and public release open.

## Phase 9.3 — authorized corrective scope

- [X] T067 [B] Diagnose one reviewed exact URL across host, API container, SafeFetcher and API; record stages/proxy presence under 30 outbound attempts; no bypass or new infrastructure.
- [X] T068 [B] Test and implement at most two validated-address connection attempts with shared deadlines, TLS/Host preservation, conservative request-budget accounting and socket/capacity release.
- [X] T069 [B] Test source toggles preserving actual review timestamps; separate configuration/readiness from review evidence and reconcile historical source register.
- [X] T070 [B] Provide reproducible diagnostics; retry API/publication/fresh-fetch/browser only after successful preflight; run PostgreSQL regressions, archive handoff, restore explicit OFFLINE/disabled policies, commit/push. Keep T066 open without its live evidence. — Preflight blocked at HTTP 490; successful live branch remains T066, not claimed complete.

**Input**: artifacts in `/specs/002-personalized-shopping-copilot/`  
**Authorization**: Phase 9/9.1 authorizes Milestone B tasks `T013–T023` and `T055–T059`. Phase 9.2 authorizes only `T060–T066` for the bounded offer pilot. Phase 10 authorizes `T024–T031` for offline Milestone C; incomplete B source tasks and Milestones D/E remain pending.  
**TDD**: behavioral tests MUST fail for the intended missing behavior before paired implementation.

## Milestone A — Conversation foundation

- [X] T001 [A] Revalidate exact existing dependency/runtime versions and record only necessary additions in `docs/tooling.md`; do not add a queue, WebSocket framework or provider framework
- [X] T002 [P] [US1] Write failing model/constraint tests for Conversation, Message, ShoppingBrief, StreamOperation and StreamEvent in `backend/tests/integration/test_copilot_models.py`
- [X] T003 [US1] Add reviewed migrations and models for T002 in `backend/analysis/models.py` and `backend/analysis/migrations/`; preserve feature 001 rows
- [X] T004 [P] [US1] Write failing owner/CSRF/lifecycle/foreign-ID API and cleanup tests in `backend/tests/api/test_conversations.py` and `backend/tests/integration/test_copilot_cleanup.py`
- [X] T005 [US1] Implement owner-scoped conversation CRUD, brief revision CAS and expired conversation/upload/event purge in `backend/analysis/api/conversations.py`, `backend/analysis/conversation/` and the existing cleanup command; preserve feature 001 expiry and owners with active conversations
- [X] T006 [P] [US1] Write failing pure brief-builder cases for self/gift/household, Persian money, unknowns, contradictions and image attribution in `backend/tests/unit/test_brief_builder.py`
- [X] T007 [US1] Implement versioned brief normalization/confirmation without product-fact invention in `backend/analysis/conversation/brief.py`
- [X] T008 [P] [US4] Write failing SSE contract tests for sequence, duplicate, reconnect gap, provisional/final, heartbeat and terminal errors in `backend/tests/api/test_stream_events.py`
- [X] T009 [US4] Implement PostgreSQL-backed operation/event publication، bounded process executor and same-origin SSE endpoint in `backend/analysis/conversation/streaming.py` and `backend/analysis/api/operations.py`; move only proxy buffering/thread-capacity prerequisites from T043 while leaving T043 open
- [X] T010 [US4] Write failing cancellation races for delete/cancel/brief-edit versus late publish in `backend/tests/integration/test_copilot_concurrency.py`, then implement operation-token guards outside network locks in `backend/analysis/conversation/operations.py`
- [X] T011 [P] [US1] Write failing React component tests for Persian conversation, brief ribbon, upload validation, stop/error and bidi in `frontend/src/features/copilot/conversation/*.test.tsx`
- [X] T012 [US1] Implement fixture-only conversation shell and API client in `frontend/src/features/copilot/conversation/` without changing default feature 001 route
- [X] T049 [US1] Write failing upload API tests for owner isolation, CSRF, MIME/signature, size/count, metadata stripping, retention and delete races in `backend/tests/api/test_copilot_uploads.py`, then implement the bounded backend upload boundary in `backend/analysis/api/uploads.py` without object-storage dependency
- [X] T051 [P] [US4] Write failing PostgreSQL regressions for final-boundary cancel/edit/delete precedence، atomic rollback، lost lease، fresh-lease reconciliation، bounded stream expiry/replay/purge، executor submission/capacity and concurrent subscriber admission in `backend/tests/`
- [X] T052 [US4] Implement consistent `Conversation → StreamOperation` locking، renewable owned leases، atomic final publication، authoritative stale/cancel reconciliation and exactly-once executor reservation release in `backend/analysis/conversation/` and mutation APIs
- [X] T053 [US4] Implement bounded/admitted SSE، authoritative replay validation/control gap، REST client reconciliation and reconnect without regeneration in `backend/analysis/api/operations.py` and `frontend/src/features/copilot/conversation/`
- [X] T054 [US4] Verify focused/full PostgreSQL suites، migration drift، frontend/browser and real NGINX cancel/reconnect/admission; update stream/OpenAPI/quickstart/operations/handoff evidence without beginning Milestone B

**Checkpoint A**: fixture conversation/brief/stream works independently; no provider or research network.

## Milestone B — Evidence foundation

- [ ] T013 [B] Complete domain terms/robots review and approve an initial allowlist in `specs/002-personalized-shopping-copilot/source-feasibility.md`; unavailable domains stay disabled — **Partial:** reviewed register and narrow Phase 9.2 pilot decision exist; general integration/reuse/retention/display uncertainties remain. Written permission is not a universal prerequisite for that bounded pilot.
- [X] T014 [P] [US2] Write failing SourcePolicy/ResearchJob/Snapshot/Product/Variant/Offer/Claim constraints and migration tests in `backend/tests/integration/test_research_models.py`
- [X] T015 [US2] Implement relational evidence entities and non-destructive migrations in `backend/analysis/models.py` and `backend/analysis/migrations/`
- [X] T016 [P] [US2] Write failing URL/SSRF/redirect/private-address/DNS-rebinding/content-type/size/time/concurrency tests in `backend/tests/unit/test_safe_fetch.py`
- [X] T017 [US2] Implement bounded allowlist fetch transport in `backend/analysis/research/fetch.py`; no browser/CAPTCHA/auth bypass
- [ ] T018 [P] [US2] Capture copyright-safe minimal fixtures for one approved source in each ready category and checksums in `backend/tests/fixtures/research/`; do not claim sports ready until direct extraction succeeds — **Partial:** appliance/electronics captured and checksummed؛ approved sports source unavailable
- [ ] T019 [P] [US2] Write failing extractor/field-provenance/freshness tests for electronics, appliance and approved sports fixture in `backend/tests/unit/test_extractors.py` — **Partial:** appliance/electronics and cache freshness covered؛ approved sports fixture unavailable
- [X] T020 [US2] Implement deterministic per-source extractors and schema validation in `backend/analysis/research/extractors/`
- [X] T021 [P] [US2] Write failing variant reconciliation tests for region, identifier, bundle, warranty and ambiguity in `backend/tests/unit/test_variant_identity.py`
- [X] T022 [US2] Implement identity/conflict handling and timed offer observations in `backend/analysis/research/identity.py`
- [X] T023 [US2] Write failing owner/CSRF start-status-cancel، bounded progress، cache/dedupe، lease renewal، stale publication، partial failure and cleanup integration tests in `backend/tests/integration/test_research_jobs.py` and API tests، then implement coordinator and typed minimal API in `backend/analysis/research/jobs.py` and `backend/analysis/api/research.py` by reusing StreamOperation/Event
- [X] T055 [P] [US2] Write failing API/PostgreSQL regressions for typed product targets، boolean/malformed validation، atomic revision/confirmation acceptance، replay after brief change and guest-wide admission in `backend/tests/api/test_research_api.py` and `backend/tests/integration/test_research_concurrency.py`
- [X] T056 [P] [US2] Write failing safe-transport regressions for bounded DNS/header/body، wire/decoded gzip، normalized paths، per-destination redirects and capacity/deadline waits in `backend/tests/unit/test_safe_fetch.py`
- [X] T057 [P] [US2] Write failing production-path controlled-source tests for fetch→extract→identity→offer/claims→events، rollback، cache/cancel، mixed outcomes and lifecycle reconciliation in `backend/tests/integration/test_research_pipeline.py`
- [X] T058 [US2] Connect validated targets to SourcePolicy، shared job budgets، SafeFetcher، deterministic extraction and guarded atomic evidence publication; synchronize ResearchJob/StreamOperation terminal transitions without enabling a public source
- [X] T059 [US2] Reassess T020–T023، run focused/full PostgreSQL and NGINX/browser verification، archive Phase 9 handoff and update contracts/tooling/quickstart/handoff with controlled-versus-public readiness truth
- [X] T060 [B] Reassess current Torob، Digikala and at most three direct Iranian merchant policies/extraction; record prohibition، documented permission، no explicit rule، access failure and technical failure separately in `source-feasibility.md`
- [X] T061 [P] [US2] Write failing adapter/normalization tests for Torob embedded offers and direct JSON-LD merchant offers، explicit IRR/IRT conversion، missing/invalid price، stock، layout drift، freshness، variant identity، seller dedup and unknown-total sorting in `backend/tests/unit/`
- [X] T062 [US2] Add the minimum offer provenance fields/migration and source-specific extraction registry، then narrowly configure reviewed exact product paths through the existing policy/fetch/publication pipeline
- [X] T063 [P] [US2] Write failing PostgreSQL/API tests for multiple offers، partial source failure، deterministic comparable-offer view، ownership/cancel/expiry/stale publication and existing request budgets، then expose the attributed offer view in research status
- [X] T064 [P] [US2] Write failing React tests for exact URL input، explicit research action، progress، live/cache/stale labels، Persian offer copy، unknown shipping/total and partial failures
- [X] T065 [US2] Implement the minimal existing-route Choice Desk offer panel and API client without implementing product ranking، alternatives، memory or AI; add mobile/desktop NGINX browser coverage
- [ ] T066 [B] Execute the bounded five-product/three-category live pilot under the 100-request phase ceiling، repeat one successful source، record actual offers/timestamps/URLs and screenshot evidence، run affected/full verification، update handoff، commit and push without staging `test.txt` — **partial:** five-product attempt and UI evidence complete; direct workspace transport yielded no successful source، so successful-source repeat and ≥3 live offers remain pending

**Checkpoint B**: only approved fixture domains yield citations; access failures remain explicit.

## Milestone C — Choice Desk

- [x] T024 [P] [US3] Write hand-authored ranking cases for budget, total cost, hard constraints, missing evidence, stale offer, gift context and ties in `backend/tests/unit/test_copilot_ranking.py`
- [x] T025 [P] [US3] Write property/exhaustive invariants for determinism, no unsupported contribution and stable ties in `backend/tests/unit/test_ranking_invariants.py`
- [x] T026 [US3] Implement `COPILOT-RANK-v0.1` pure pipeline in `backend/analysis/ranking/` and persist versioned ChoiceSet results
- [x] T027 [P] [US3] Write API contract tests for ChoiceSet attribution, citations, coverage and unknown total-cost components in `backend/tests/api/test_choice_desk.py`
- [x] T028 [US3] Implement current Choice Desk serializer/API in `backend/analysis/api/choices.py`
- [x] T029 [P] [US3] Write React tests for cards/table/mobile disclosure, source drawer, long Persian/bidi, partial/final and keyboard semantics in `frontend/src/features/copilot/choice-desk/*.test.tsx`
- [x] T030 [US3] Implement Choice Desk Concept 2 in `frontend/src/features/copilot/choice-desk/` using installed design skill plus project RTL/accessibility overlay and no new UI framework
- [x] T031 [US3] Add Playwright journeys for 390/1440 viewports, keyboard, 200% zoom, stream stop and axe serious/critical zero in `tests/e2e/copilot-choice-desk.spec.ts`

**Checkpoint C**: fixture-based multi-category Choice Desk is deterministic and accessible; still no live provider.

Phase 10 evidence: canonical PostgreSQL 260/260; React 19/19; typecheck/lint/build; real NGINX Playwright at
390/1440 with sources, keyboard, 200% zoom, brief invalidation/recompute, real cancellation and axe serious/critical zero.
Fixtures are explicitly synthetic/captured; public-source T066 and other incomplete source tasks remain pending.
Implementation corrections within C: category/count/attribution contract closure, migration-test schema cleanup,
JSON-null empty GET, short-stream test synchronization, scoped RTL/zoom and modal focus. No Milestone D work.

## Milestone D — Opt-in memory and OpenAI readiness

Phase 11 authorizes T032–T041 only, including visible settings/profile navigation, temporary conversations,
memory-only export, provisional configurable lifecycle, credential revision invalidation, documented catalog
filtering, existing-ledger operation/session caps, PostgreSQL tests and real NGINX offline browser verification.
FR-023/024/035/066/067 map to T032–T033/T041; FR-025/065/068 to T034–T036/T040/T041;
FR-020/022/026–030/068 to T037–T040. Feature 001 T039 and Milestone E remain pending.

- [x] T032 [P] [US5] Write failing memory consent/candidate/confirmation/context/isolation/delete/export tests in `backend/tests/api/test_preference_memory.py`
- [x] T033 [US5] Implement default-off preference memory and review/correct/delete APIs in `backend/analysis/memory/`
- [x] T034 [D] Evaluate maintained encryption options against target-host key operations and record license/version/recovery decision in `docs/tooling.md` and `docs/decisions.md`; do not create custom crypto
- [x] T035 [P] [US5] Write failing credential write-only, encryption, masking, rotation, deletion, log/redaction and missing-master-key tests in `backend/tests/unit/test_user_credentials.py`
- [x] T036 [US5] Implement envelope-encrypted OpenAI credential storage with master key outside DB/image/Git in `backend/analysis/ai/credentials.py`
- [x] T037 [P] [US4] Revalidate official model IDs/capabilities/pricing/data policy and freeze an allowlist/schema/cost policy in `specs/002-personalized-shopping-copilot/openai-readiness.md`
- [x] T038 [P] [US4] Write stubbed Responses streaming adapter tests for structured output, image input, usage/request ID, timeout/retry/cancel/malformed/error in `backend/tests/unit/test_openai_copilot.py`
- [x] T039 [US4] Implement direct OpenAI-only adapter behind existing seam in `backend/analysis/ai/openai_copilot.py`; `store=false`, no AvalAI fallback and no live calls in unsupported region
- [x] T040 [US5] Write factory/settings tests proving offline default, missing configuration fail-closed, Iran eligibility blocked despite key and operation/session cost cap in `backend/tests/test_copilot_configuration.py`, then wire non-secret settings
- [x] T041 [P] [US5] Add masked key/memory controls and billing-vs-ChatGPT copy tests/UI in `frontend/src/features/copilot/memory/`

**Checkpoint D**: stubbed integration only. Live OpenAI remains blocked until official region eligibility and separate spending authorization.

Phase 11 evidence: final PostgreSQL suite 283/283; fresh-schema focused run 22/22; frontend 21/21, lint/typecheck/build;
real NGINX settings + two-conversation journeys passed at 390 and 1440, including keyboard, 200% zoom and axe.
Choice Desk regression found a one-pixel RTL skip-link overflow; explicit in-viewport positioning fixed it,
and both viewport regressions passed without weakening assertions. Frontend tests/lint/build were rerun after CSS changed.
Earlier browser failures (locator/readiness synchronization and a loaded-run timeout) are retained in the handoff,
not counted as successes. No provider/source calls; feature001 T039, T042–T048/T050 and T066 remain pending.

## Phase 11.1 — contextual assistant closure

Authorization is limited to T071–T077. AI remains mock by default, research remains OFFLINE and all provider/source
transports are stubbed. Milestone E, T066, feature001 T039 and live quality/coverage gates remain open.

- [x] T071 [P] [US4] Write failing bounded-context tests for history/brief/ChoiceSet/evidence/cost/image/consented-memory inclusion, temporary/context isolation, explicit-over-memory precedence, deterministic truncation and critical-context limited state in `backend/tests/unit/test_copilot_context.py`
- [x] T072 [US4] Implement the pure context assembler and additive StreamOperation manifest/fingerprint migration; pin and revalidate turn/brief/generation/settings/ChoiceSet/evidence/upload/memory context in `backend/analysis/ai/copilot_context.py` and the existing operation boundary
- [x] T073 [P] [US4] Write failing answer-plan/parser/semantic evidence tests and installed-SDK model-list transport tests, including malformed/unsupported blocks, prompt-like source data, unavailable selection and zero implicit provider calls
- [x] T074 [US4] Implement the narrow answer contract, deterministic Persian renderer, evidence/value/freshness/candidate validation and explicit gated `models.list()` refresh seam without free-form factual publication
- [x] T075 [P] [US4] Write failing real worker/SSE regressions for supplied budget, «چرا گزینه دوم؟», enjoyment, unknown technical comparison, supported alternative, missing evidence, temporary memory exclusion, explicit override and stale context races; stub only external provider transport
- [x] T076 [US4] Wire meaningful safe-lead/validated-block streaming without provider typing delay and add three labelled deterministic in-app scripted demonstrations through the same assembler/worker/publication path; update React status/copy tests only as required
- [x] T077 [US4] Run scoped/full PostgreSQL and frontend verification plus real NGINX mobile/desktop demo journeys; archive Phase 11 handoff and update contracts/operations/quickstart/handoff with stub-versus-live limitations, then commit/push related files only

**Checkpoint D.1**: contextual behavior is verified through synthetic/stubbed application paths only. Live OpenAI
quality, account model access and live market coverage remain unevaluated.

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

`A → B evidence models/controlled fixtures → offline C`; public extraction and T066 gate live coverage, not offline C. T055–T057 block T058 and T058 blocks T059. Memory work in D depends on A, adapter work depends on A streaming, and E depends on selected completed milestones. T009 may implement only NGINX buffering/timeouts and Gunicorn request-thread capacity required to verify A; T043 remains open for full graceful-shutdown/production rehearsal criteria. T049 follows T003/T005 and blocks image use. T013 gates general source integration; FR-055 separately authorizes the narrow factual pilot. T034 blocks credential implementation. T037/T040 and official region support block live AI calls. T050 follows A/D data ownership. T047 never completes merely from a key. Feature 001 `T039` remains independent and pending.

## Implementation strategy

Implement only a separately authorized milestone. Stop at each checkpoint and use offline fixtures first. No task here is complete in Phase 7; planning artifacts are not executable evidence.
