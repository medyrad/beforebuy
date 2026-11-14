# تحویل Phase 2 — بستن rubric و برنامه‌ریزی فنی

## وضعیت و مرز فاز

rubric قطعی categorical با شناسه `PDA-CAT-v0.3` برای technical planning تصویب و artifactهای canonical
`$speckit-plan` برای feature موجود `001-purchase-decision-analysis` ساخته شدند. هیچ feature دوم، `tasks.md`،
application scaffold، dependency manifest، browser runtime، code-intelligence tool یا deployment service ایجاد/نصب
نشد. implementation همچنان مجاز نیست.

handoff قبلی در `docs/archive/phase-1.1-handoff.md` آرشیو شد.

## اصلاحات دقیق rubric

- خروجی مبهم `strong or moderate` حذف شد. justification دقیقاً یکی از
  `JUSTIFICATION_SUPPORTED`, `DISCRETIONARY_CLEAR`, `WEAK_OR_NONE`, `JUSTIFICATION_UNKNOWN`, `CONTRADICTORY`
  است و با `JUS-01..06` به‌ترتیب انتخاب می‌شود.
- budget، justification، target fit و tradeoff چهار dimension مستقل و exactly-one هستند. report mode فقط metadata
  است.
- `REPAIR_NOTED` و `WAIT_NOTED` فقط action flag و پیشنهاد بررسی‌اند؛ feasibility، preference یا sufficiency را ثابت
  نمی‌کنند و supported purchase را override نمی‌کنند.
- `RECONSIDER_OR_WAIT` فقط از evidence صریح target mismatch یا `NO_CLEAR_BENEFIT` می‌آید. discretionary با tradeoff
  حل‌نشده `INSUFFICIENT_CONTEXT` است، نه diagnosis منفی.
- missing/unknown هرگز به weak/no benefit تبدیل نمی‌شود. `JUS-06` fallback برابر scoped unknown است.
- above-budget همیشه primary headline است؛ justification، target fit، urgency و unknownها همچنان visible می‌مانند.
- همان normalized inputs + rubric version همان dimensionها، matched ruleها، outcome، unknownها و actionها را می‌سازد.
  AI/prose/retry/rating در نتیجه deterministic دخالت ندارند.
- edit input revision تازه و recomputation کامل با همان rule version می‌سازد. late response برای revision قدیمی،
  deleted/expired analysis یا rubric دیگر discard می‌شود.
- retry فقط اگر canonical visible payload و mode دقیقاً برابر باشد report revision/rating را حفظ می‌کند؛ تغییر prose،
  evidence، outcome یا mode report revision تازه و rating خالی می‌سازد.
- workload اکنون «۸ primary input field» و «تا ۱۱ question/input prompt» است، نه تعداد قطعی interaction/action.
  completion time فقط usability target آینده است و نتیجه اندازه‌گیری‌شده نیست.

## جدول ordered نهایی primary outcome

dimensionها اول مستقل محاسبه می‌شوند. ردیف‌های زیر از بالا به پایین بررسی و اولین match دقیقاً یک headline می‌دهد.

| Priority / rule | شرط | Primary outcome | اطلاعات حفظ‌شده |
|---|---|---|---|
| 1 / `OUT-01` | budget = `ABOVE_BUDGET` | `BUDGET_MISMATCH` | justification، fit، urgency و unknownها |
| 2 / `OUT-02` | justification = `CONTRADICTORY` یا `JUSTIFICATION_UNKNOWN` | `INSUFFICIENT_CONTEXT` | budget و target fit معلوم |
| 3 / `OUT-03` | target fit = `USER_REPORTED_MISMATCH` | `RECONSIDER_OR_WAIT` | need و budget ممکن است supported بمانند |
| 4 / `OUT-04` | justification = `WEAK_OR_NONE` | `RECONSIDER_OR_WAIT` | budget unknown/known و target state |
| 5 / `OUT-05` | discretionary + tradeoff = `UNRESOLVED` | `INSUFFICIENT_CONTEXT` | enjoyment شکست/diagnosis نیست |
| 6 / `OUT-06` | budget unknown + justification supported | `PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN` | fit مستقل و budget unknown |
| 7 / `OUT-07` | budget unknown + discretionary + acknowledged | `DISCRETIONARY_CHOICE_BUDGET_UNKNOWN` | fit مستقل |
| 8 / `OUT-08` | budget within + justification supported | `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` | selected model تأیید نمی‌شود |
| 9 / `OUT-09` | budget within + discretionary + acknowledged | `DISCRETIONARY_CHOICE_WITHIN_BUDGET` | selected model مستقل |
| 10 / `OUT-10` | هر ترکیب valid باقی‌مانده | `INSUFFICIENT_CONTEXT` | fallback total بدون ساخت evidence |

coverage table و headlineهای واقعی فارسی برای supported/repair-noted/target-mismatch/urgent-above-budget در
`decision-rubric.md` قرار دارند. scenarioها و acceptanceها working-device new-use، minor benefit، serious unclear،
enjoyment unresolved، no-device discretionary، unknown state/budget، contradiction، mismatch و simultaneous matches
را پوشش می‌دهند.

## بررسی‌های واقعی و محدودیت آن‌ها

- enumeration تازه همه `6 × 7 × 3 × 3 × 3 = 1134` ترکیب categorical ورودی مدل specification را طی کرد؛ بعد از
  ordered dimension evaluation برای هر مورد یک justification/tradeoff و بعد یک primary outcome وجود داشت و uncovered
  state صفر بود.
- دو raw justification overlap (`UNKNOWN + PERSONAL_ENJOYMENT` و `UNKNOWN + NO_CLEAR_BENEFIT`) عمداً با تقدم
  `JUS-02` به unknown حل می‌شوند؛ در فضای کامل ۵۴ ترکیب ورودی را دربرمی‌گیرند. overlapهای raw outcome با ترتیب
  `OUT-01..10` حل می‌شوند (۵۵۰ ترکیب raw multi-match) و final outcome یگانه است.
- OpenAPI YAML parse شد؛ لینک‌های محلی Markdown، نبود artifact ممنوع `tasks.md`/manifest، markerهای clarification و
  identifier/wordingهای قدیمی بررسی شدند.
- این‌ها verification مدل specification و consistency artifactها هستند. چون application وجود ندارد، build، migration،
  API test، browser test، security test، latency، completion time، AI quality/cost، backup restore و production capacity
  اجرا یا اندازه‌گیری نشده‌اند.

## معماری فنی

topology برنامه‌ریزی‌شده: `browser → web static/reverse proxy → Django/DRF api → PostgreSQL`. Compose سه service
`web`, `api`, `db` دارد. build چندمرحله‌ای frontend فقط asset static را به gateway می‌دهد؛ Vite preview production
نیست. `/` و `/api/` same-origin هستند و CORS لازم نیست.

repository یک monorepo است؛ backend یک Django modular monolith با یک domain app اولیه `analysis` دارد. rule engine
تابع خالص و مستقل از ORM/clock/network/AI است. Redis، Celery، WebSocket، microservice، Kubernetes، vector database،
event sourcing، generic repository/entity framework، provider registry، agent framework، account/JWT و SSR انتخاب
نشدند.

baseline برنامه: Python `3.12.x`، Django `5.2.17` LTS، DRF `3.18.1`، React `19.3.x`، TypeScript `5.9.x`،
Vite `8.1.x` و PostgreSQL `18.x`. نسخه‌های exact frontend هنگام lockfile implementation pin می‌شوند؛ این‌ها
انتخاب مستندی‌اند و package نصب‌شده/benchmark‌شده در workspace نیستند.

## مدل داده و lifecycle

- `GuestContext`: UUID opaque، created/absolute expiry؛ شناسه فقط در Django database session.
- `Analysis`: guest FK، input revision، rubric/schema version، product/price/budget، latest typed answers، creation،
  immutable expiry و updated timestamp.
- `CurrentReport`: one-to-one current-only؛ report revision، mode، primary outcome، dimensionها، matched ruleها، typed
  embedded evidence/unknown/action/prose و canonical hash.
- `UsefulnessFeedback`: حداکثر یک rating ۱..۵ برای analysis + current report revision + mode.
- answer/evidence embedded JSONB هستند چون فقط atomic با current state خوانده/جایگزین می‌شوند و query مستقل مصوب
  ندارند؛ ownership، expiry و feedback رابطه‌ای و indexed باقی می‌مانند. full revision history ذخیره نمی‌شود.

draft پیش از report در browser می‌ماند. اولین success یا clearly labeled limited report، Analysis و CurrentReport را
atomic persist و retention را آغاز می‌کند؛ failure بدون report چیزی persist نمی‌کند. expiry همیشه creation + 90 days
و non-sliding است. command روزانه purge با target حداکثر ۲۴ ساعت کافی است و queue لازم ندارد.

## قرارداد API

source یگانه contract فایل `specs/001-purchase-decision-analysis/contracts/openapi.yaml` است:

- `GET /api/v1/session`: bootstrap guest context و CSRF cookie.
- `GET/POST /api/v1/analyses`: list و create/evaluate/persist.
- `GET/PATCH/DELETE /api/v1/analyses/{id}`: read، edit+recompute و delete.
- `POST /api/v1/analyses/clear`: clear same-browser history.
- `POST /api/v1/analyses/{id}/reanalysis`: retry current input revision.
- `PUT/DELETE /api/v1/analyses/{id}/feedback`: create/change/remove rating current report.

موفقیت‌ها `200/201/204`، validation برابر `400`، CSRF برابر `403`، missing/foreign/deleted/expired همگی `404`، stale
input/report revision برابر `409` و failure بدون هیچ displayable report برابر `503` است. error shape ثابت
`{error:{code,message,field_errors?,current_input_revision?}}` دارد. schema و request/response example داخل همان OpenAPI
هستند و توضیح موازی contract نگهداری نمی‌شود.

## مالکیت، revision، deletion و expiry

- Django server-side session یک guest UUID را نگه می‌دارد؛ analysis ID هرگز authorization نیست. همه operationها
  owner + active expiry filter دارند. same-browser یعنی با از دست‌رفتن cookie recovery وجود ندارد.
- session cookie در production `HttpOnly`, `Secure`, `SameSite=Lax` است؛ CSRF cookie/token و `X-CSRFToken` برای همه
  unsafe operationها لازم‌اند. session پس از bootstrap touch نمی‌شود تا lifetime نلغزد؛ Analysis expiry authoritative
  است.
- publish با compare-and-swap روی owner، analysis، input revision، rubric و active expiry انجام می‌شود. cancellation
  best-effort است؛ correctness به update شرطی متکی است.
- delete hard-delete current state/feedback است. late worker اگر row حذف/expired/revised باشد صفر row update می‌کند و
  حق insert/resurrection ندارد. access در لحظه expiry بسته است، مستقل از زمان physical purge.
- logs فقط request ID/status/latency/error code دارند؛ answer text، session/CSRF، rating و raw AI request/response وارد
  log نمی‌شوند.

## AI boundary

یک interface کوچک `ExplanationGenerator` request ساخت‌یافته شامل evidence typed، deterministic result frozen، زبان و
schema version می‌گیرد. response bounded JSON است. validator هم وجود evidence ID و هم سازگاری claim type/content با
evidence و rule را می‌سنجد؛ ID معتبر با محتوای بی‌ربط support نیست. model name قابلیت تلفن نمی‌سازد و user text data
است، نه instruction.

mock فقط با label صریح برای test/dev است. provider/model، timeout، bounded retry، cost ceiling و evaluation set پیش از
real adapter gate هستند. timeout/malformed/unsupported/contradictory output فقط limited deterministic report می‌دهد؛
AI outcome را عوض نمی‌کند. real adapter و live evaluation پیش از live readiness الزامی‌اند.

## مهارت‌ها و tooling

- استفاده‌شده: `purchase-regret-project` برای boundary/evidence، `$speckit-specify` برای correction artifact موجود،
  `$speckit-plan` برای plan canonical، `$speckit-checklist` برای review بعد plan، و
  `verification-before-completion` برای commandهای تازه. `$speckit-analyze` اجرا نشد چون به `tasks.md` نیاز دارد و
  ساخت tasks در این phase ممنوع بود.
- frontend: `react-best-practices` و `web-design-guidelines` از Vercel Labs در commit
  `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62`، version `1.0.0` و MIT ارزیابی و برای trigger implementation انتخاب
  شدند؛ نصب نشدند. scope فقط React+Vite است و Next.js/Vercel requirement رد می‌شود؛ overlay فارسی/RTL لازم است.
- backend: local skill مناسب نبود؛ سه candidate public بررسی شدند. به‌دلیل scope گسترده، dependency یا فرض JWT/Django
  قدیمی‌تر انتخاب نشدند. درست پیش از backend implementation یک skill محلی متمرکز validation، ownership/permission،
  session/CSRF، migration، ORM query، API contract و tests ساخته می‌شود؛ اکنون نصب/ساخته نشد.
- browser: Playwright CLI + Skills رسمی در trigger browser verification ارزیابی می‌شود؛ MCP فقط برای capability لازم.
- code intelligence: تا vertical slice نماینده deferred و حداکثر دو candidate مقابل native search benchmark می‌شوند.

منابع primary و version rationale در `research.md` ثبت‌اند: [Django release/support](https://www.djangoproject.com/download/)،
[Django sessions](https://docs.djangoproject.com/en/5.2/topics/http/sessions/)،
[DRF SessionAuthentication/CSRF](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication)،
[DRF releases](https://github.com/encode/django-rest-framework/releases)،
[Vite static deployment](https://vite.dev/guide/static-deploy.html)،
[PostgreSQL versioning](https://www.postgresql.org/support/versioning/)،
[Docker Compose readiness](https://docs.docker.com/compose/how-tos/startup-order/)،
[Vercel Labs skills](https://github.com/vercel-labs/agent-skills) و
[Playwright MCP/CLI direction](https://github.com/microsoft/playwright-mcp). هیچ tooling نصب‌نشده به‌عنوان available
گزارش نشده است.

## artifactهای Phase 2

- `specs/001-purchase-decision-analysis/plan.md`
- `specs/001-purchase-decision-analysis/research.md`
- `specs/001-purchase-decision-analysis/data-model.md`
- `specs/001-purchase-decision-analysis/contracts/openapi.yaml`
- `specs/001-purchase-decision-analysis/quickstart.md`
- `specs/001-purchase-decision-analysis/checklists/technical-plan.md`
- اصلاح `spec.md`, `decision-rubric.md`, `questionnaire.md`, `scenarios.md`, `acceptance.md`
- اصلاح `docs/product-brief.md`, `docs/decisions.md`, `docs/tooling.md`, `README.md`

## gateهای باقی‌مانده

### blocker برنامه‌ریزی

هیچ انتخاب substantive باز که مانع review این plan باشد باقی نمانده است.

### gateهای implementation/readiness، نه blocker برنامه‌ریزی

1. review و approval این plan، سپس اجرای جداگانه `$speckit-tasks`؛ implementation فقط با مجوز phase بعد.
2. pin/install project-scoped dependencies و skillهای triggerشده؛ اجرای TDD و contract tests.
3. انتخاب real AI provider/model و timeout/retry/token/cost limits؛ live evaluation قبل readiness.
4. ارزیابی Playwright CLI + Skills و اجرای browser journeyهای repeatable.
5. تعیین backup retention/erasure، اجرای restore واقعی و rollback/migration rehearsal قبل production.
6. measurement واقعی latency، questionnaire completion، capacity و operational cost؛ targetها نتیجه محسوب نمی‌شوند.
7. code-intelligence benchmark فقط پس از vertical slice و فقط اگر benefit concrete نشان دهد.

Technical plan ready for review; implementation has not started.
