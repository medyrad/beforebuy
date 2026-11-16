# Implementation Plan: دستیار شخصی خرید

**Branch**: `002-personalized-shopping-copilot` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

Current follow-up FR-096 / T105–T106: extend only scripts/diagnose-research.py with reviewed-target selection and stage timing; reuse actual SafeFetcher and extractor, preserve all transport validation. Direct probes use matching headers, validated pinned IP and verified TLS; no ambient proxies. Ceiling12 separate from historical ledgers. Stop after matching host/container failures; otherwise extraction must precede normal API publication. No DB/key needed for portable diagnostics; no changes to UI/manual/provider scope. T066 remains its original broader gate.

Current real-market checkpoint: FR-093–095, T102–T104 only; AI issues are deferred. Reuse SafeFetcher and reviewed adapters, ceiling30 attempts. If blocked, add one synchronous owner/revision-guarded manual-offer endpoint under existing choices, using ResearchJob/SourceSnapshot/Variant/Offer and source marker USER-ENTRY-v1. No new catalog, background worker or network in manual submission. Keep original currency/amount in Offer; snapshot retrieval_time is claimed observation, created_at is server entry. Distinct USER_REPORTED observation/mode labels; no EvidenceClaim technical facts. Ranking excludes this attribution; a separate price-only table inside the same Choice Desk may compare reported offers. Exact variant grouping requires explicit confirmation; no inferred identity merging. Preserve source review/enable flags and secret startup. No real prices will be invented if sources fail.

T096 correction supersedes the previous feasibility-before-implementation boundary: build technical integration
independently (FR-092), leaving T101 actual activation/evaluation pending. Reuse provider encryption and worker/SSE;
pin Baidu ERNIE free/baidu at the official Chat Completions endpoint. A singleton database attempt counter survives
guest/conversation deletion and limits the whole initial pilot to ten generation attempts, without resetting by day.
Record each attempt in AIInvocation, retain returned USD cost separately from local estimates. No automatic retries.
Separate service/route eligibility configuration, informed synthetic-data consent, saved key and tested account.
Explicit connection testing consumes one attempt and creates a new temporary synthetic-only conversation on success.
Only that conversation can use the free route while normal runtime remains mock. Strip memory/evidence/images from
pilot context, reject uploads, preserve ownership/manifest/lease publication checks and allow no implicit fallback.

Historical bounded follow-up (superseded by FR-092 above): T098–T100, FR-090/091. Research two exact OpenRouter free routes before any adapter.
If eligibility/privacy cannot be established, document the precise unresolved question and leave T096 pending;
do not build another unusable provider. Independently fix native select typography in existing CSS, isolate Latin
model IDs, and use real NGINX computed-style/keyboard/mobile regression tests and screenshots. Preserve existing
secret-aware startup, credentials, database volumes and mock/OFFLINE runtime. No new framework or paid usage.

Historical settings correction scope: T093–T095 and T097 (FR-088/089); T096 was deferred in that delivery. Clear credential state on every provider transition,
provide recoverable reload on partial failures, guard save/delete by provider identity and serialize updates.
Use a synchronous ref lock for same-render events and a lifecycle generation for every asynchronous continuation;
late responses cannot release the current lock or load/publish another credential. No new provider in delivery.
Restore the existing local keyring through the secret overlay, never generate a replacement. Add a scoped startup
wrapper requiring the externally configured keyring path so subsequent documented starts retain the mount.
Free-provider research is separate from approval: no live route until Iran eligibility and fixed model/data contract
are established. Existing mock/OFFLINE and spending gates remain unchanged.

Historical bounded UX authorization: T086–T092 only. FR-082–087 supersede the historical default-route restriction,
not retention or live gates. Add JSON conversational state to ShoppingBrief (pending budget) and reply actions to
Message. Acceptance validates question/revision under existing locks, records explicit bounded fields and advances
revision before operation creation. Final publication binds actions to its own message; context includes pending
state for stale protection. Model prose is not converted into arbitrary actions. Clear history reuses ownership
and deletion semantics. Frontend uses a viewport flex/grid shell, independently scrolling thread/desk, native dialog
history and generation tokens for asynchronous completions. Existing React, SVG, Vazirmatn and Playwright suffice.

Beforebuy در feature جدید از flow ثابت تلفن به shopping copilot فارسی/RTL تبدیل می‌شود: brief گفت‌وگویی، پژوهش on-demand محدود، evidence field-level، رتبه‌بندی deterministic و Choice Desk. معماری modular monolith و same-origin حفظ می‌شود. Milestone A conversation/brief، upload و streaming fixture را پیاده کرده و Milestone B pipeline کنترل‌شده را متصل کرده است. Phase 9.2 فقط Torob و direct merchantهای محدود را از همان pipeline فعال، offer normalization/dedup را اضافه و یک offer panel حداقلی در Choice Desk نشان می‌دهد؛ ranking محصول، memory و provider همچنان milestoneهای بعدی‌اند.

## Phase 12 execution boundary

Product-lead authorization removes OpenAI exclusivity without weakening eligibility or evidence gates. The selected
adapter is the fixed GapGPT Chat Completions streaming path for `gapgpt-deepseek-v4.1-flash`; AvalAI is documented as
a non-automatic fallback only. Existing OpenAI ciphertext remains in its current table. A new minimal provider-bound
credential record serves GapGPT, and settings pin provider/model. No registry, arbitrary base URL, self-hosted runtime,
purchase or live call is introduced. The provider emits bounded JSON text because exact-model JSON Schema/tool support
is undocumented; server validation/rendering remains authoritative. Natural acknowledgement/one next question may be
model-authored only inside a narrow non-factual contract; factual blocks still require validated application evidence.

## Phase 9.3 corrective boundary

Only T067–T070 are authorized. Diagnose an existing reviewed URL before attributing failure to address selection.
Try at most two distinct prevalidated addresses before HTTP send, with a shared deadline and a bounded share of
remaining connection time per address. Every fallback consumes the existing request/domain budget; no extra retry
budget or proxy is introduced. Preserve actual source review dates independently from policy toggles. Live retries
require successful SafeFetcher preflight; T066 remains pending until extraction/publication/fresh-repeat evidence exists.

## Technical Context

Phase 11.1 authorizes T071–T077 only. Add a pure bounded context assembler under the existing AI seam. It emits a
provider payload plus a non-secret manifest/fingerprint; StreamOperation pins only identifiers, revisions, hashes and
expiry/freshness anchors, never duplicated prose. Assembly keeps critical brief constraints/contradictions/unknowns
whole, truncates optional history deterministically oldest-first with an explicit marker, and fails to a limited local
answer before any transport call when required context cannot fit. Current explicit brief criteria take precedence;
temporary conversations and disabled consent exclude memory.

The Responses schema becomes a small answer-plan contract: answer type, controlled lead key and at most three typed
blocks referencing current candidate, criterion and evidence IDs. Validation checks candidate identity, deterministic
group/outcome/check values, attribution, source freshness and cost fields before a Persian renderer emits factual text.
No free-form model prose is treated as evidence. A safe context-aware lead may stream provisionally; validated rendered
blocks follow validation and the final stored message remains authoritative. OpenAI operations receive no artificial
typing delay. The mock path uses the same assembler/renderer with deterministic scripted plans for labelled local demos.

The installed OpenAI SDK 3.49.0 `client.models.list()` is wrapped behind a narrow transport seam. Explicit refresh is
region/credential gated and intersects returned IDs with the documentation catalog; settings/key GET/PUT never call it.
Live eligibility remains unconditionally blocked for the confirmed Iran deployment. No provider/source calls, new
service, vector database, agent framework or production test bypass are introduced.

Phase 11 supersedes the historical Phase 10 scope below only for T032–T041. Add guest-scoped CopilotSettings,
PreferenceMemory and envelope-encrypted UserCredential; reuse AIInvocation/LiveBudgetLedger for reservation and
settlement. Credential master keyring is a runtime file secret; offline starts without it. Documentation-based
OpenAI catalog is not account validation; IR users/backend are blocked independently of configuration checkboxes.
Memory is explicit structured criteria only, scoped by category and recipient; temporary conversation is immutable
at creation. Proposals require confirmed source briefs; reuse requires unconfirmed target brief/CAS and cannot
overwrite current criteria. Source deletion cascades derived preferences. FR-066 retention is provisional development
configuration, not approved public policy. Tests use synthetic credentials and SDK/HTTP stubs only.
Session reserved/spent micro-USD aggregates live on GuestContext and are maintained by the same LiveBudgetLedger,
with Guest -> daily window -> invocation locking. Metadata purge and key replacement do not reset session spending.
Migrations 0011–0014 are additive; back up non-empty development data before applying them. Production key-management,
retention approval and live activation remain separate gates. Runtime Responses events never carry raw keys or JSON.

Phase 10 authorizes T024–T031 only. Completed evidence models and controlled fixtures unblock offline Milestone C;
T066/public-source success gates live coverage, not this implementation. Milestone B remains partial. Add a validated
comparison profile to ShoppingBrief and an immutable ChoiceSet JSON result (items embedded, no redundant ChoiceItem
table). Same owner-scoped evidence adapter and pure categorical engine serve synthetic, captured and future live data.
No network/LLM calls or memory/credential work. Existing Concept 2 tokens/layout remain; comparison cards and source
disclosure occupy the main workspace, with merchant offers nested under their exact variant.

**Language/Version**: Python `3.12.x`، TypeScript `5.9.x`  
**Primary Dependencies**: Django `5.2.16`, DRF `3.17.1`, React `19.3.1`, Vite `8.3.8`; Pillow `13.0.0` فقط برای decode/re-encode امن upload؛ safe fetch از Python 3.12 stdlib با socket pinning استفاده می‌کند و dependency runtime تازه ندارد  
**Storage**: PostgreSQL 18؛ object/file storage جدید تا سنجش upload volume اضافه نمی‌شود  
**Testing**: backend suite، Vitest، Playwright، fixture HTTP transport و contract tests  
**Target Platform**: یک Linux server کوچک با Docker Compose و same-origin HTTPS  
**Project Type**: web application / modular monolith  
**Performance Goals**: acknowledgement محلی message زیر 500ms p95 در rehearsal؛ first fixture stream event زیر 2s؛ ranking بیست گزینه زیر 100ms  
**Constraints**: کاربران/backend ایران؛ direct OpenAI live blocked؛ GapGPT live requires independent credential/spend gate؛ bounded research؛ بدون queue/Redis/WebSocket پیش‌فرض؛ secrets فقط backend  
**Scale/Scope**: pilot کم‌حجم، سه category fixture، یک محصول موردنظر و حداکثر سه محصول جایگزین در Choice Desk؛ merchant offerها جدا و limits source/job صریح

## Constitution Check

| Gate | Design evidence | Result |
|---|---|---|
| Lean scope | milestoneهای A–E؛ fetch on-demand/capped؛ بدون crawler fleet/queue/vector DB | PASS |
| Traceability | FRها به contract، model و tasks map می‌شوند؛ unknownها gate می‌مانند | PASS |
| Deterministic rules | [ranking-evidence-rules.md](ranking-evidence-rules.md) hard filter/arithmetic/tie را مالک است | PASS |
| Evidence/streaming | provenance field-level، source snapshot و provisional/final boundary | PASS |
| Privacy/secrets | memory opt-in؛ credential encrypted/masked؛ retention per entity | PASS |
| Persian/RTL | [choice-desk-design.md](choice-desk-design.md) keyboard، bidi، mobile و stream announcements | PASS |
| Low-cost deployment | topology موجود؛ SSE؛ bounded jobs؛ no new service | PASS |
| Verification | fixtures، contract، cancellation، ownership، source failure و browser journeys | PASS |

Post-design re-check: service مستقل و dependency speculative اضافه نمی‌شود. GapGPT credential/spend validation، OpenAI region و source permission gateهای بازند، نه فرض پنهان.

## Architecture and Boundaries

```text
Browser Choice Desk / Conversation
        │ same-origin REST + SSE
        ▼
NGINX web ── /api/ ──> Django/DRF
                         ├─ conversation + brief
                         ├─ bounded research coordinator
                         ├─ deterministic ranking/evidence publisher
                         ├─ GapGPT Chat Completions adapter (live gated)
                         ├─ optional OpenAI Responses adapter (region blocked)
                         └─ PostgreSQL
```

- REST command state را می‌سازد؛ SSE فقط event همان operation را می‌دهد. reconnect با `Last-Event-ID` و GET state reconcile می‌شود. `next_sequence - 1` بالاترین sequence صادرشده است و replay validation به retained row اول متکی نیست.
- execution mechanism در Milestone A یک `BoundedThreadPoolExecutor` process-local با دو worker و queue ظرفیت چهار است.
  `POST message` ابتدا Message/StreamOperation را atomic ثبت می‌کند و فقط با `transaction.on_commit` submit می‌شود.
  executor هیچ source of truth ندارد: worker با conditional update در PostgreSQL operation `PENDING` را claim،
  `lease_owner` و `lease_expires_at` ثبت و پیش از publication آن را تمدید/بازبینی می‌کند. final message، دو final event و
  state completion در یک transaction با lock order `Conversation → StreamOperation` منتشر می‌شوند. حداکثر دو operation
  `PENDING|RUNNING` برای هر guest پذیرفته می‌شود؛ overflow پیش از ساخت operation با `429` رد می‌شود.
- هر application process executor مستقل دارد، اما claim/sequence/cancel/token در PostgreSQL مشترک است. process crash
  ممکن است `PENDING` ثبت‌شده اما submit‌نشده یا `RUNNING` leaseدار باقی بگذارد. status/reconciliation و cleanup، lease
  منقضی را به terminal `INTERRUPTED` تبدیل می‌کنند؛ operation خودکار restart نمی‌شود و publish دوباره مجاز نیست.
  controlled retry فقط operation تازه با idempotency key تازه می‌سازد.
- browser disconnect فقط subscriber را قطع می‌کند و operation ادامه می‌یابد؛ cancel صریح زیر همان lock order فوراً
  terminal می‌شود. SSE هیچ execution را start/restart نمی‌کند و lock در generation یا stream wait نگه داشته نمی‌شود.
  هر connection حداکثر 45 ثانیه باز است، expiry/stale state را authoritative reconcile می‌کند و سپس client با همان
  Last-Event-ID دوباره وصل می‌شود؛ gap به REST reconciliation ختم می‌شود، نه regeneration.
- Gunicorn از worker class `gthread` با دو process و چهار request thread استفاده می‌کند؛ executor دو thread جدا دارد.
  admission semaphore جداگانه در هر process فقط دو subscriber SSE را می‌پذیرد و دو request thread را برای cancel/status
  آزاد می‌گذارد؛ thread count به‌تنهایی admission control محسوب نمی‌شود. overflow با `429 STREAM_CAPACITY_REACHED` رد
  می‌شود و release در close/disconnect idempotent است. این bound در proxy smoke آزموده می‌شود.
- source response untrusted است؛ fetch/extract از prompt boundary جداست.
- research executor و admission از fixture conversation executor جداست، اما PostgreSQL operation/event همان source of truth می‌ماند. outbound semaphore دو request در هر process است، نه global؛ یک active research job per guest با row/constraint logic enforce می‌شود.
- safe fetch ابتدا exact policy/path را می‌سنجد، DNS را resolve و همهٔ addressها را public validate می‌کند و connection را به یک IP تأییدشده pin می‌کند؛ TLS SNI/certificate و Host hostname اصلی‌اند و proxy environment مصرف نمی‌شود. redirect از ابتدا دوباره validate می‌شود.
- budget اولیه: 3 domain، 5 content page/domain، 2 redirect/request، 20 total HTTP request، 2 MiB decoded/page، 20s/request، 60s/job، pacing یک ثانیه/domain. raw cache 24h non-sliding و freshness مستقل است.
- Phase 9.1 target contract برابر source ID + exact product URL است؛ domain-only discovery پیاده نمی‌شود. acceptance زیر Guest→Conversation lock و evidence publication زیر Conversation→Operation→ResearchJob→SourcePolicy lock کوتاه انجام می‌شود؛ fetch/extract بیرون transaction است.
- یک `FetchBudget` از limits persisted برای کل job sequential ساخته می‌شود و request/redirect/wire/decoded measurement را میان sourceها حمل می‌کند. test transport connector می‌تواند socket محلی کنترل‌شده را جایگزین کند، اما resolver/policy production public-address validation را دور نمی‌زند و runtime flag برای تضعیف SSRF وجود ندارد.
- OpenAI built-in web search در MVP منبع بازار authoritative نیست.
- model از catalog allowlisted پس از revalidation capability/price برای ID دقیق انتخاب می‌شود.

## Milestones

| Milestone | Outcome | Exit evidence |
|---|---|---|
| A — Conversation foundation | conversation/message/brief، guest ownership، bounded fixture executor، upload boundary و fixture streaming | contract + ownership + reconnect/cancel/interruption tests |
| B — Evidence foundation | policy/fetch/extract/variant/offer برای سه fixture category | extraction + SSRF/limit/failure tests |
| B.2 — Real offer pilot | exact URL، Torob/direct merchant adapters، normalized offers و minimal in-app panel | stubbed adapter/regression tests + bounded five-product live observation + NGINX browser evidence |
| C — Choice Desk | ranking deterministic، total cost، comparison responsive | invariant/component/browser tests |
| D — Personalization & OpenAI readiness | memory opt-in، encrypted key، adapter stub و gates | secret/memory/model tests؛ live calls zero |
| D.1 — Contextual assistant closure | bounded context، validated answer blocks، meaningful safe streaming و synthetic in-app demos | real worker/SSE tests with transport stub + mobile/desktop NGINX demo |
| E — Production rehearsal & pilot gate | SSE proxy/restart/backup/retention و allowlist review | Compose rehearsal؛ approvals جدا |

## Project Structure

### Documentation

```text
specs/002-personalized-shopping-copilot/
├── spec.md
├── plan.md
├── research.md
├── source-feasibility.md
├── choice-desk-design.md
├── ranking-evidence-rules.md
├── migration-coexistence.md
├── data-model.md
├── quickstart.md
├── contracts/{openapi.yaml,stream-events.md}
├── checklists/requirements.md
└── tasks.md
```

### Source layout (Milestone A subset implemented)

```text
backend/analysis/{api,conversation,research,ranking,memory,ai}/
frontend/src/features/copilot/{conversation,choice-desk,memory,services}/
backend/tests/{api,integration,unit}/
frontend/src/**/*.test.tsx
tests/e2e/copilot-milestone-a.spec.ts
```

**Structure Decision**: repository و deployment surface فعلی حفظ می‌شود؛ moduleهای feature داخل backend/frontend موجود اضافه می‌شوند.

## Capability Map

| State | Capability |
|---|---|
| Reuse | React/Vite/RTL/Vazirmatn، session ownership/CSRF، PostgreSQL، operation token/generation epoch، cost-ledger pattern، Compose/NGINX/backup |
| Build | conversation/brief، SSE event log، source policy/fetch/extract، product/variant/offer/evidence، ranking، Choice Desk، memory، credential |
| Coexist | feature 001 routes/data/UI تا cutover؛ T039 باز می‌ماند |
| Supersede for 002 | phone questionnaire primary UX، phone rubric global ranker، AvalAI runtime، fixed 90-day policy as universal |

## Release Gates

1. هر source فقط پس از policy review و extraction fixture وارد allowlist می‌شود.
   Phase 9.2 narrow pilot برای `/p/` ترب و exact product pathهای direct merchant با pace حداقل 2s، freshness 6h، raw 24h و attribution مجاز است؛ این تصمیم blanket license یا full-market coverage نیست.
2. GapGPT selected path تا credential validated و مجوز هزینه fail closed است؛ direct OpenAI برای ایران region-blocked
   باقی می‌ماند. user key هیچ gate را bypass نمی‌کند و هیچ provider fallback خودکاری وجود ندارد.
3. retention Milestone A و raw/evidence Milestone B مصوب است؛ retention مربوط به memory/credential، backup-erasure operations، encryption-key operations و target host پیش از pilot بسته می‌شوند.
4. هیچ milestone این feature، `T039` feature 001 را کامل نمی‌کند.

## Complexity Tracking

هیچ deviation ثبت نشد. SSE به‌جای WebSocket، in-process bounded job به‌جای queue و relational evidence به‌جای vector DB انتخاب شد.
