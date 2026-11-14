# Implementation Plan: دستیار شخصی خرید

**Branch**: `002-personalized-shopping-copilot` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

Beforebuy در feature جدید از flow ثابت تلفن به shopping copilot فارسی/RTL تبدیل می‌شود: brief گفت‌وگویی، پژوهش on-demand محدود، evidence field-level، رتبه‌بندی deterministic و Choice Desk. معماری modular monolith و same-origin حفظ می‌شود. streaming با SSE و state authoritative در PostgreSQL طراحی می‌شود؛ memory opt-in و credential متعلق به کاربر مرزهای جدا دارند. Phase 7 فقط artifacts را تولید می‌کند و implementation شروع نمی‌شود.

## Technical Context

**Language/Version**: Python `3.12.x`، TypeScript `5.9.x`  
**Primary Dependencies**: Django `5.2.16`, DRF `3.17.1`, React `19.3.1`, Vite `8.3.8`; dependency تازه در این phase اضافه نمی‌شود  
**Storage**: PostgreSQL 18؛ object/file storage جدید تا سنجش upload volume اضافه نمی‌شود  
**Testing**: backend suite، Vitest، Playwright، fixture HTTP transport و contract tests  
**Target Platform**: یک Linux server کوچک با Docker Compose و same-origin HTTPS  
**Project Type**: web application / modular monolith  
**Performance Goals**: acknowledgement محلی message زیر 500ms p95 در rehearsal؛ first fixture stream event زیر 2s؛ ranking بیست گزینه زیر 100ms  
**Constraints**: کاربران/backend ایران؛ OpenAI direct live blocked؛ bounded research؛ بدون queue/Redis/WebSocket پیش‌فرض؛ secrets فقط backend  
**Scale/Scope**: pilot کم‌حجم، سه category fixture، حداکثر 20 option در Choice Desk و limits source/job صریح

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

Post-design re-check: service مستقل و dependency speculative اضافه نمی‌شود. OpenAI region و source permission gateهای بازند، نه فرض پنهان.

## Architecture and Boundaries

```text
Browser Choice Desk / Conversation
        │ same-origin REST + SSE
        ▼
NGINX web ── /api/ ──> Django/DRF
                         ├─ conversation + brief
                         ├─ bounded research coordinator
                         ├─ deterministic ranking/evidence publisher
                         ├─ OpenAI Responses adapter (disabled by region default)
                         └─ PostgreSQL
```

- REST command state را می‌سازد؛ SSE فقط event همان operation را می‌دهد. reconnect با `Last-Event-ID` و GET state reconcile می‌شود.
- coordinator داخل process با timeout/cancellation/limit کار می‌کند؛ worker جدا فقط پس از measurement و تصمیم تازه.
- source response untrusted است؛ fetch/extract از prompt boundary جداست.
- OpenAI built-in web search در MVP منبع بازار authoritative نیست.
- model از catalog allowlisted پس از revalidation capability/price برای ID دقیق انتخاب می‌شود.

## Milestones

| Milestone | Outcome | Exit evidence |
|---|---|---|
| A — Conversation foundation | conversation/message/brief، guest ownership، fixture streaming | contract + ownership + reconnect/cancel tests |
| B — Evidence foundation | policy/fetch/extract/variant/offer برای سه fixture category | extraction + SSRF/limit/failure tests |
| C — Choice Desk | ranking deterministic، total cost، comparison responsive | invariant/component/browser tests |
| D — Personalization & OpenAI readiness | memory opt-in، encrypted key، adapter stub و gates | secret/memory/model tests؛ live calls zero |
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

### Planned source code (not created in Phase 7)

```text
backend/analysis/{api,conversation,research,ranking,memory,ai}/
frontend/src/features/copilot/{conversation,choice-desk,memory,services}/
backend/tests/{api,integration,unit}/
frontend/src/**/*.test.tsx
tests/e2e/copilot.spec.ts
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
2. OpenAI برای ایران تا پشتیبانی رسمی/قابل اتکا fail closed است؛ user key bypass نیست.
3. retention، backup erasure، encryption-key operations و target host پیش از pilot بسته می‌شوند.
4. هیچ milestone این feature، `T039` feature 001 را کامل نمی‌کند.

## Complexity Tracking

هیچ deviation ثبت نشد. SSE به‌جای WebSocket، in-process bounded job به‌جای queue و relational evidence به‌جای vector DB انتخاب شد.
