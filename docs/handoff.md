# تحویل Phase 9.1 — تکمیل و راستی‌آزمایی bounded research pipeline

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline بازبینی‌شده:** `5b4bb551f71f0c444c082859329290f0d2273541`  
**branch:** `002-personalized-shopping-copilot`  
**وضعیت:** pipeline منبع کنترل‌شده کامل و verify شد؛ پوشش source عمومی همچنان pending است  
**taskهای کامل این فاز:** `T055–T059`  
**taskهای partial و باز:** `T013`, `T018`, `T019`  
**خارج scope و باز:** Milestoneهای C–E، memory/credential/live AI و هر دو feature-specific `T039`

## نتیجه و مرز فاز

در Phase 9.1 مسیر واقعی request معتبر → policy → bounded fetch → deterministic extraction → identity → offer/claims →
atomic evidence publication به coordinator موجود متصل شد. این مسیر با HTTP server کنترل‌شده و PostgreSQL واقعی verify
شد، اما هیچ source عمومی enable یا فراخوانی نشد. Choice Desk/ranking Milestone C، memory، credential، provider call،
خرید، public deployment و live AI تغییری نکردند. حذف نامرتبط `test.txt` حفظ و از commit کنار گذاشته می‌شود. handoff
Phase 9 در `docs/archive/phase-9-handoff.md` آرشیو شد.

## Spec Kit و truth taskها

- feature رسمی همان `002-personalized-shopping-copilot` است؛ `.specify/extensions.yml` وجود نداشت و checklist
  `requirements.md` برابر 16/16 بود.
- `$speckit-analyze` چهار gap High اولیه را تأیید کرد: coordinator متصل نبود، acceptance payload/revision را اتمیک
  تثبیت نمی‌کرد، evidence/progress یک publication unit نبود و limits persisted execution counters واقعی نبودند.
- اصلاحات در `FR-050–FR-054`، plan، data model، OpenAPI و `T055–T059` ثبت شدند. تحلیل پس از اصلاح هیچ Critical/High
  تازه‌ای نداشت؛ gapهای source عمومی و Milestoneهای آینده به‌عمد باز ماندند.
- `$speckit-implement` فقط `T055–T059` را اجرا کرد. `T020–T023` پس از اتصال production path و regressionهای تازه همچنان
  complete هستند. `T013/T018/T019` برای permission و sports fixture/extractor partial باقی ماندند.

## قرارداد acceptance و API

- input اصلی `targets` است. هر LIVE target باید `{source_id, url}` با exact product URL داشته باشد؛ domain-only با
  422 رد می‌شود. fixture می‌تواند URL-null باشد و compatibility محدود `source_ids` فقط برای FIXTURE حفظ شده است.
- boolean revision، list/object تو‌در‌تو، field اضافی، URL نامعتبر و source/hostname mismatch پاسخ typed 4xx دارند.
- admission زیر `GuestContext → Conversation` lock، ownership/expiry، confirmed brief، expected revision، target-mode
  association، idempotency و یک active job per guest را اتمیک می‌سنجد. race دو request واقعی API فقط یکی را 202 کرد
  و دیگری 429 گرفت.
- idempotent replay قبل از reinterpretation state تازه بررسی می‌شود؛ brief تغییرکرده revision job قدیمی را عوض نمی‌کند.
- status شامل targets، pinned brief revision، `current_for_brief`، request/redirect/wire/decoded counters، snapshot،
  failure code، offer و claim attribution است. GET/SSE کار شبکه را شروع یا تکرار نمی‌کند.

## transport و budget واقعی

- SafeFetcher همان Python stdlib 3.12 و IP-pinned connection را حفظ می‌کند؛ TLS SNI/certificate و Host اصلی‌اند، همهٔ
  DNS answerها باید public باشند، proxy/cookie/credential و private endpoint ممنوع‌اند.
- DNS executor/capacity، pacing، outbound capacity، connect/TLS/header/body، request و job همگی remaining deadline
  دارند. testهای server کنترل‌شده slow-header و slow-drip نشان دادند انتظار از deadline عبور نمی‌کند.
- path پیش از prefix check normalize می‌شود و encoded dot/slash/backslash/percent ambiguity رد می‌شود. redirect مقصد
  rule مستقل host/port/path دارد.
- gzip malformed، truncated و concatenated/composite رد می‌شود. سقف wire compressed و decoded مستقل است. non-2xx،
  MIME نامعتبر، request/domain/redirect cap و DNS failure code صریح دارند.
- یک `FetchBudget` از limits persisted برای کل job sequential ساخته می‌شود. request/redirect/wire/decoded واقعی، از
  جمله مصرف پیش از failure، روی ResearchJob ثبت می‌شوند. semaphore دو outbound per process است و global معرفی نمی‌شود.

## publication، identity، cache و lifecycle

- fetch/extraction خارج transaction انجام می‌شود. publication با lock order
  `Conversation → StreamOperation → ResearchJob → SourcePolicy` دوباره owner، lease، cancel، conversation expiry،
  brief revision، generation epoch، job state و current policy را می‌سنجد.
- snapshot، product/variant، offer، claims، counters، `evidence.published` و `research.progress` یک per-source transaction
  هستند. fault injection rollback نشان داد snapshot/event/identity orphan باقی نمی‌ماند.
- identity فقط با common identifier سازگار merge می‌شود؛ name-only ambiguity یا identifier/region/attribute conflict
  variant جدا می‌سازد. offer timestamp و price/currency/seller/availability جدا persist می‌شوند.
- cache فقط در همان conversation، با raw غیرمنقضی و policy دوباره‌قفل‌شده reuse می‌شود. cancel پیش از cache publication
  snapshot تازه‌ای ایجاد نکرد.
- submission failure، cancel، worker exception، stale lease/brief/expiry و completion، ResearchJob و StreamOperation را
  اتمیک یا با status/admission reconciliation همگرا می‌کنند. restart کار network را تکرار نمی‌کند و quota stale آزاد
  می‌شود.
- migration `0007_research_targets_and_transport_counters` legacy `source_ids` را به targetهای URL-null تبدیل و
  `redirect_rules`, `targets`, `wire_bytes`, `redirect_count` را بدون حذف یا reset داده اضافه کرد.

## controlled-source evidence و source عمومی

integration test یک policy فقط-تستی `products.example` می‌سازد. resolver یک IP public مستندشده برمی‌گرداند و connector
مرزی تست socket را به loopback server می‌فرستد؛ production policy هیچ localhost/private bypass ندارد. مسیر واقعی API،
policy، fetcher، JSON-LD extractor، identity، offer/claims، PostgreSQL و events اجرا شد:

- یک request، صفر redirect، wire/decoded مثبت؛ Host و exact `/products/e1` مطابق policy؛
- snapshot `EXTRACTED`، SKU attributed، offer تومان با seller/availability و outcome `SUCCESS`؛
- یک `evidence.published` و progress اتمیک؛ rollback/cancel بدون evidence نیمه‌کاره.

این سند quality/permission source عمومی را نتیجه نمی‌گیرد. enabled public source دقیقاً صفر است؛ public request،
provider/model call و paid activity Phase 9.1 همگی صفر بودند. Philips/Technolife/Torob همچنان clarification کتبی
permission/retention/display/rate می‌خواهند و sports source مجاز وجود ندارد.

## verification تازه

- focused research/API/PostgreSQL/transport/extractor/identity/migration: 47 discovered/run، 47 passed، skipped/failed/
  error صفر در 11.086s. slow-header/slow-drip disconnectهای مورد انتظار در test handler جذب شدند؛ رفتار production تغییر نکرد.
- پس از review نهایی lock شدن SourcePolicy در acceptance و refresh پاسخ submission، مجموعهٔ affected API/lifecycle/
  concurrency/pipeline دوباره اجرا شد: 24/24 passed در 8.558s.
- canonical backend از root: `./scripts/test-backend.sh --keepdb --verbosity 1` → 229 discovered/run، 229 passed،
  skipped/failed/error صفر در 44.388s.
- `manage.py check` بدون issue؛ `makemigrations --check --dry-run` → `No changes detected`؛ compileall، OpenAPI YAML و
  `git diff --check` موفق.
- migration 0007 روی development Compose اعمال شد؛ volume/database reset نشد و سه service healthy ماندند.
- Playwright رسمی 1.65.1 image digest
  `sha256:1507cbfc550a63a6b7396791ca4f00df17beb56342d2447b3f106c306f525579` علیه NGINX
  `127.0.0.1:58080`: 3/3 passed در 14.4s (desktop/accessibility/fixture stream، mobile/keyboard، legacy route).
  اجرای نخست بدون `NODE_PATH` پیش از discovery متوقف شد؛ اجرای دوم با `host.docker.internal` به‌درستی توسط ALLOWED_HOSTS
  رد شد (1/3 pass). معیار نهایی از host networking و Host مجاز استفاده کرد؛ allowlist تضعیف نشد.
- controlled pipeline smoke در suite PostgreSQL: API → real local HTTP transport → extractor → DB → status/events
  موفق بود. runtime research در Compose همچنان `OFFLINE` است.

## gateهای باقی‌مانده

1. `T013`: قرارداد روشن permission، retention، display/attribution و rate برای source عمومی.
2. `T018/T019`: sports source مجاز، fixture حداقلی checksummed و direct extraction test.
3. public-source controlled rollout باید جداگانه approved شود؛ موفقیت synthetic server مجوز source نیست.
4. Milestone C ranking/Choice Desk و Milestoneهای D/E مجوز مستقل می‌خواهند.
5. feature 001 `T039` و feature 002 live-AI gateها pending هستند؛ این فاز full-product convergence نیست.

## Git

فقط code/test/migration/spec/contracts/docs مرتبط Phase 9.1 stage می‌شوند. `.env`، secret، database، dump، log، cache،
Playwright artifact و حذف نامرتبط `test.txt` وارد commit نمی‌شوند. push فقط به branch جاری و origin موجود، بدون force،
merge یا remote تازه انجام می‌شود.

**Milestone B pipeline verified with controlled sources — public source coverage still pending.**
