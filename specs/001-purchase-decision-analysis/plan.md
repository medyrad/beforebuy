# Implementation Plan: تحلیل تصمیم خرید تلفن همراه

**Branch**: `001-purchase-decision-analysis` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: feature specification و rubric پیاده‌شده `PDA-CAT-v0.3`. milestoneهای M1/M2 پذیرفته شده‌اند؛ Phase 5
فقط M3 adapter/evaluation را مجاز می‌کند و M4 deferred می‌ماند.

## Summary

یک وب‌اپ فارسی و RTL، guest-first و same-origin ساخته می‌شود که هشت فیلد اصلی و حداکثر سه prompt پیگیری را
می‌گیرد، rubric خالص و نسخه‌دار را اجرا می‌کند و دقیقاً یک outcome همراه dimensionها، evidence، unknownها و
actionها برمی‌گرداند. React + TypeScript + Vite رابط استاتیک را می‌سازد؛ Django + DRF یک modular monolith و
PostgreSQL داده کمینه را میزبانی می‌کنند؛ یک gateway سبک فایل‌های استاتیک را سرو و `/api/` را به Django proxy
می‌کند. Docker Compose استقرار تک‌سرور را با سه service مستقل `web`, `api`, `db` نگه می‌دارد.

## Technical Context

**Language/Version**: Python `3.12.x`؛ TypeScript `5.9.x`؛ JavaScript target مدرن browser  
**Primary Dependencies**: M1 resolved: Django `5.2.16` LTS، Django REST Framework `3.17.1`، psycopg `3.3.6`،
gunicorn `23.0.0`؛ M2 baseline React `19.3.x`، TypeScript `5.9.x` و Vite `8.3.x`؛ patchهای دقیق frontend
در `frontend/package-lock.json` pin می‌شوند  
**Storage**: PostgreSQL `18.x`؛ Django database sessions؛ JSONB فقط برای answer/evidence payloadهای
schema-versioned و بدون نیاز query رابطه‌ای  
**Testing**: Django test runner + DRF APIClient؛ Vitest + Testing Library؛ Playwright CLI برای journeyهای
مرورگر پس از ارزیابی trigger آن؛ contract و rubric exhaustive tests  
**Target Platform**: مرورگرهای evergreen با mobile-first RTL؛ Linux container روی یک سرور کوچک  
**Project Type**: monorepo web application، modular monolith backend، static SPA frontend  
**Performance Goals**: evaluation خالص rubric زیر `100 ms` در test نماینده؛ API غیر-AI زیر `500 ms p95`
در staging کوچک؛ completion پرسش‌نامه در مسیر عادی هدف محصول است و تا usability test «اندازه‌گیری‌شده» گزارش
نمی‌شود  
**Constraints**: guest-only در MVP؛ same-origin؛ retention مطلق ۹۰ روز؛ purge حداکثر ۲۴ ساعت پس از expiry؛
بدون Redis/Celery/microservice؛ AI حق تغییر deterministic result ندارد؛ no resurrection بعد delete/expiry  
**Scale/Scope**: یک category (تلفن)، یک questionnaire، چهار dimension، ده rule outcome، history آخرین state،
یک rating جاری؛ ظرفیت اولیه تک‌سرور و workload کم/نامشخص، بدون ادعای benchmark production

### Phase 5.3 accounting correction

PostgreSQL دو scope را جدا نگه می‌دارد: `AILiveBudgetWindow` روزانه برای deployment و یک
`AIEvaluationAuthorization` ثابت برای allowance اولیهٔ ۱۰۰٬۰۰۰ تومان. reserve هر دو row را در transaction کوتاه
lock می‌کند؛ network بیرون transaction می‌ماند. `AIInvocation` metadata sanitized را پس از حذف guest نگه می‌دارد،
attemptهای معلوم/نامعلوم را جدا settle می‌کند و recovery صریح برای reservation رهاشده دارد. runner artifact را
پیش از call و پس از هر case atomically checkpoint می‌کند و rejection پیش از call را zero-attempt incomplete evidence
می‌نویسد. هیچ queue، billing subsystem یا provider abstraction تازه اضافه نمی‌شود.

## Constitution Check

*GATE: پیش از research و دوباره پس از design بررسی شد؛ همه gateها pass هستند.*

| Principle / gate | Design evidence | Result |
|---|---|---|
| Lean Scope | سه service ساده؛ بدون queue/cache/orchestration؛ provider abstraction فقط یک protocol کوچک | PASS |
| Traceability | API و testها به `FR-*`, `AC-*`, `PDA-CAT-v0.3` و schema version وصل می‌شوند | PASS |
| Deterministic scoring | engine تابع خالص، ordered، نسخه‌دار و exhaustively enumerable است؛ AI ورودی آن نیست | PASS |
| Evidence-grounded AI | contract ساخت‌یافته، evidence type/content validation، stale-result rejection و limited fallback | PASS |
| Privacy/minimal collection | guest context opaque؛ latest state؛ بدون identity، fingerprint یا raw provider payload | PASS |
| Persian/RTL/accessibility | `lang=fa`, `dir=rtl` از root؛ semantic forms، focus/error tests و نمایش اعداد دوزبانه | PASS |
| Low-cost deployment | Compose تک‌سرور، PostgreSQL persistent volume، health checks، migration/backup gates | PASS |
| Verification before completion | unit/contract/integration/browser layers تعریف شده؛ exploration جایگزین test نیست | PASS |

Post-design re-check: مدل داده history کامل، provider registry، event bus یا repository layer اضافه نمی‌کند. JSONB
فقط برای payloadهایی انتخاب شده که atomic خوانده می‌شوند؛ ownership، feedback و lifecycle رابطه‌ای و queryable
باقی مانده‌اند. deviation قانون اساسی وجود ندارد.

## Architecture and Boundaries

### Request and deployment flow

`browser → web (static + reverse proxy) → api (Django/DRF) → db (PostgreSQL)`.

- build frontend در image stage انجام و فقط asset خروجی به `web` منتقل می‌شود؛ dev server Vite production نیست.
- `web` همان origin را برای SPA و `/api/` ارائه می‌کند؛ cookie و CSRF cross-origin نمی‌شوند.
- `api` migration را به‌عنوان step صریح release اجرا می‌کند، نه به‌صورت هم‌زمان در همه workerها.
- health checkهای `db`, `api`, `web` و dependency conditionهای Compose readiness را قابل مشاهده می‌کنند.

### Guest ownership and CSRF

- نخستین bootstrap یک `GuestContext` با UUID تصادفی، `access_expires_at` و `generation_epoch=0` ایجاد و شناسه آن
  را فقط در Django database session ذخیره می‌کند. cookie دارای `HttpOnly`, `Secure` در production و
  `SameSite=Lax` است.
- session/access lifetime هنگام bootstrap ۹۰ روز است. فقط persist موفق یک **analysis جدید** آن را تا
  `max(current access expiry, new analysis.expires_at)` تمدید می‌کند؛ بنابراین analysis ساخته‌شده در روز ۸۹ تا
  روز ۱۷۹ قابل دسترسی می‌ماند. visit، edit، retry و feedback نه session/access lifetime و نه expiry خود analysis
  را تمدید نمی‌کنند. محدودیت/حذف زودتر cookie توسط browser و فقدان cross-device recovery صریحاً مستند می‌شود.
- همه querysetها ابتدا با `guest_context_id` و سپس active lifecycle filter می‌شوند. foreign/deleted/expired ID
  همگی `404` می‌دهند تا وجود رکورد افشا نشود.
- اتکا به DRF `SessionAuthentication` برای guest anonymous ممنوع است، چون DRF برای anonymous request الزام CSRF
  ایجاد نمی‌کند. `CsrfViewMiddleware` فعال می‌ماند و base view همه endpointهای unsafe با decorator استاندارد Django
  `csrf_protect` محافظت می‌شود؛ bootstrap با `ensure_csrf_cookie` token را صادر می‌کند. SPA token را از cookie
  قابل‌خواندن گرفته و در `X-CSRFToken` با `credentials: same-origin` می‌فرستد. `ALLOWED_HOSTS` و Origin/
  `CSRF_TRUSTED_ORIGINS` با origin deployment محدود می‌شوند؛ CORS لازم نیست.

### Persistence and lifecycle

- draft تا وقتی report موفق یا `RULE_BASED_LIMITED` تولید نشده در state مرورگر است. `POST /analyses` validation،
  deterministic evaluation و تولید report را انجام می‌دهد و فقط report قابل‌نمایش را در transaction persist می‌کند.
- `created_at` اولین persisted report و `expires_at = created_at + 90 days` است. هیچ operation آن را تغییر نمی‌دهد.
- command روزانه `purge_expired_analyses` رکوردهای expired و cascadeهایشان را پاک می‌کند؛ alert اگر lag از ۲۴ ساعت
  عبور کند. direct access بدون انتظار purge بسته می‌شود.
- initial create پیش از network/provider call، `generation_epoch` مهمان را snapshot می‌کند. publish در transaction
  کوتاه `GuestContext` را `SELECT ... FOR UPDATE` می‌گیرد، epoch را دوباره می‌سنجد و سپس Analysis+Report را insert
  می‌کند. clear-history در transaction همان row را lock، epoch را atomic increment و analysisها را delete می‌کند.
  در هر ترتیب serialization، create قدیمی یا پیش از clear حذف می‌شود یا پس از clear به‌علت epoch mismatch publish
  نمی‌شود؛ check-then-insert غیراتمی مجاز نیست.
- retry/edit هنگام شروع، یک `report_operation_token` تازه را با شرط input/report revision ثبت می‌کند و network را
  بیرون transaction اجرا می‌کند. publish فقط با token جاری، owner، input revision، rubric و active expiry ممکن است؛
  بنابراین retry قدیمی‌تر نمی‌تواند report/rating retry جدیدتر را overwrite کند. delete hard-delete است.
- cleanup روزانه ابتدا analysisهای expired، سپس GuestContextهای بدون analysis با `access_expires_at <= now` و سپس
  Django sessionهای expired را پاک می‌کند؛ cron/systemd timer کافی است و queue اضافه نمی‌شود.
- فقط latest answers/report/evidence نگهداری می‌شود. revision identifier برای concurrency و rating ownership است،
  نه audit history.

### Deterministic engine

- `normalize → validate → evaluate_dimensions → select_primary_outcome → derive_unknowns_actions → canonicalize`.
- توابع domain از Django model، clock، network، locale rendering و AI مستقل‌اند و value objectهای immutable می‌گیرند.
- rule tableها identifier و rubric version صریح دارند؛ اولین outcome match انتخاب می‌شود ولی همه matched evidence/rule
  referenceهای لازم برای explanation حفظ می‌شوند.
- exhaustive parameterized test همه ترکیب‌های categorical معتبر را enumerate و exact-one dimension/outcome،
  precedence و boundary examples را بررسی می‌کند. invalid monetary inputs جدا property/table-tested می‌شوند.

### AI boundary

- تنها seam اولیه یک `ExplanationGenerator.generate(request) -> response` است؛ mock deterministic و یک adapter واقعی
  آینده همین protocol را اجرا می‌کنند. registry چند-provider یا agent framework وجود ندارد.
- request `PDA-EXPLAIN-v1` شامل target label محدود و صریحاً untrusted، normalized evidence با ID/type/value، frozen
  deterministic result، unknown/action IDها و schema version است؛ session/ownership data، rating و raw prompt در آن نیست.
  evidence مربوط به intended use و urgency بدون تغییر rubric افزوده می‌شود تا AI نقش توضیحی واقعی داشته باشد.
- response یک JSON schema محدود از outcome echo، unknown acknowledgement، headline و حداکثر سه explanation block
  با evidence/rule reference است. validator هم reference existence، mapping نوع claim به نوع evidence، exact outcome
  و حفظ unknownها را کنترل می‌کند. این validator semantic entailment متن آزاد را تضمین نمی‌کند؛ این محدودیت با
  evaluation مستقل و review انسانی مدیریت می‌شود و برای عبور مدل validation شل نمی‌شود.
- mock report صریحاً mode `MOCK_ASSISTED` دارد؛ `AI_ASSISTED_SUCCESS` فقط برای provider واقعی است و rating/metric
  mock با live-AI مخلوط نمی‌شود. direct OpenAI برای deployment ایران غیرفعال است. adapter انتخابی Phase 5.2
  AvalAI Responses API با مدل دقیق `gpt-5.6-luna` و SDK موجود OpenAI `3.49.0` روی base URL مستند AvalAI است؛
  Responses support از مستندات خود AvalAI آمده، نه از ادعای generic compatibility. live mode پیش‌فرض خاموش
  می‌ماند. timeout `8s`، حداکثر دو attempt، request byte/token upper-bound، output ceiling `512` token و per-guest
  روزانه `10` هستند. budget deployment بدون تنظیم صریح fail closed است و evaluation cap کل `100,000` تومان است. timeout، quota، schema
  failure یا unsupported claim به report صریح `RULE_BASED_LIMITED` می‌انجامد؛ outcome تغییر نمی‌کند.
- reservation سراسری و per-guest count با PostgreSQL و lock کوتاه انجام می‌شود؛ provider call بیرون transaction است.
  reservation بدبینانه همه attemptهای مجاز را پیشاپیش حساب می‌کند و circuit پس از failureهای متوالی موقتاً باز می‌شود.
- publication به input revision bind است. cancellation best-effort است و correctness به conditional publish متکی است.

### API and UI

- قرارداد canonical در [contracts/openapi.yaml](./contracts/openapi.yaml) است. validation errorها field-specific و
  machine-readable هستند؛ optimistic conflicts `409` و unavailable ownership/lifecycle `404` است.
- SPA چهار state اصلی دارد: questionnaire، generating، report، history. edit از latest answers prefill می‌کند و report
  قبلی را تا موفق‌شدن replacement stale نشان می‌دهد؛ retry exact-same payload rating را حفظ و content/mode change آن
  را پاک می‌کند.
- componentها outcome را از dimension cards جدا نشان می‌دهند تا target fit با justification/budget خلط نشود.
- root فارسی/RTL است؛ ترتیب بصری با DOM semantic سازگار، focus بعد error/generation مدیریت و statusها با text علاوه
  بر رنگ بیان می‌شوند. تومان و ورودی ارقام فارسی/لاتین طبق spec normalize می‌شوند.

## Test Strategy

1. **Domain unit**: normalization پول، همه `JUS/FIT/TRD/ALT/OUT` ruleها، exact-one/totality، canonical hashing.
2. **API contract**: schema examples، status/error shape، CSRF، owner isolation، list/detail/edit/retry/delete/feedback.
3. **Persistence integration**: atomic first report، guest lifetime extension only on new analysis، non-sliding analysis
   expiry، purge cascade، clear/create epoch serialization، competing retry token، stale publish، delete during
   generation و rating clearing/preservation؛ race testها روی PostgreSQL با barrier/event و بدون sleep اصلی.
4. **AI contract**: mock/live separation، success ساخت‌یافته، malformed/incomplete، unknown evidence، claim ناسازگار،
   outcome contradiction، prompt-injection-like target text، timeout/rate-limit/transient retry، exhaustion، credential
   missing، quota/circuit rejection و publication دیررس/حذف/expiry.
5. **Frontend component**: Persian labels/errors، RTL semantics، keyboard/focus، loading/failure/limited states، dimension
   independence و rating ownership.
6. **Browser journey**: happy path، invalid money، follow-up cap، history/edit/retry، AI fallback، delete/expiry. CLI
   repeatable اولویت دارد؛ MCP فقط اگر inspection تعاملی لازم باشد.
7. **Deployment**: image/build config، Compose health، migrations، static route/API proxy، backup/restore و rollback rehearsal
   پیش از production. هیچ‌کدام در Phase 2 اجراشده تلقی نمی‌شوند.

## Project Structure

### Documentation (this feature)

```text
specs/001-purchase-decision-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── decision-rubric.md
├── questionnaire.md
├── scenarios.md
├── acceptance.md
├── spec.md
└── checklists/
    ├── requirements.md
    └── technical-plan.md
```

`tasks.md` در Phase 3 با `$speckit-tasks` ساخته شده است؛ در Phase 5.2 فقط taskهای `T049–T052` مجازند.
headline و reasonهای پایه از engine/evidence قطعی ساخته می‌شوند؛ AI فقط explanation تکمیلی می‌دهد. هزینه با یک
ماژول مشترک از کل instructions/input/schema/framing margin و output bound رزرو و با usage واقعی idempotent settle
می‌شود. ارزیابی automatic و human را جدا نگه می‌دارد و هیچ semantic معیار اندازه‌گیری‌نشده‌ای را pass/zero نمی‌کند.

### Planned source code (repository root)

```text
backend/
├── manage.py
├── config/
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── analysis/
│   ├── api/
│   ├── domain/
│   │   ├── engine.py
│   │   ├── money.py
│   │   └── rules.py
│   ├── ai/
│   │   ├── contracts.py
│   │   ├── validator.py
│   │   └── generator.py
│   ├── management/commands/purge_expired_analyses.py
│   ├── migrations/
│   ├── models.py
│   └── services.py
└── tests/
    ├── api/
    ├── integration/
    └── unit/

frontend/
├── index.html
├── src/
│   ├── app/
│   ├── components/
│   ├── features/analysis/
│   ├── pages/
│   ├── services/api/
│   └── styles/
└── tests/

deploy/
├── api.Dockerfile
├── web.Dockerfile
└── web.conf

tests/
└── e2e/

compose.yaml
```

**Structure Decision**: یک monorepo با دو build surface و یک backend modular monolith. `analysis` تنها Django app
دامنه‌ای اولیه است؛ لایه‌های domain/API/AI مرزهای تست هستند، نه serviceهای مستقل. gateway استاتیک برای same-origin
و static production serving انتخاب شده و business logic ندارد.

## Release and Operations Gates

- secrets فقط environment/secret store؛ production debug خاموش، allowed hosts و trusted origins صریح.
- migration forward و rollback-compatible release؛ backup قبل migration consequential.
- PostgreSQL volume، automated backup schedule، restore test و backup retention/deletion policy باید پیش از production
  در decision record بسته شوند. حذف فوری backup هنوز ادعا نمی‌شود.
- structured logs فقط request ID، status، latency و error code؛ answer text، session key، CSRF، raw AI payload و rating
  در log ممنوع.
- AI adapter واقعی فقط پس از model/provider، timeout، retry، cost ceiling و evaluation set مصوب فعال می‌شود.

## Complexity Tracking

هیچ violation قانون اساسی پذیرفته نشده است. gateway سومین service Compose است، اما deployment platform یا business
service جدا نیست؛ برای static serving صحیح و same-origin proxy لازم است و از افزودن Node production server جلوگیری
می‌کند.
