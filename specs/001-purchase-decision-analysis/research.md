# Phase 2 Technical Research

**Date**: 2026-11-14  
**Scope**: تصمیم‌های لازم برای plan؛ هیچ dependency یا runtime برنامه نصب نشد.

## Selected baseline

| Need | Decision | Alternatives considered | Rationale / evidence status |
|---|---|---|---|
| Backend framework | M1 resolved: Django `5.2.16` LTS + DRF `3.17.1` | proposal `5.2.19` + `3.18.3`؛ Django `6.1.3` feature release | metadata رسمی availability proposal را تأیید کرد، اما download workspace مکرراً timeout شد. نسخه‌های انتخابی exact، سازگار با Python 3.12 و از cache رسمی موجود reproducible بودند. Django 5.2 همچنان LTS تا آوریل ۲۰۲۸ است. |
| Frontend | React `19.3.x` + TypeScript `5.9.x` + Vite `8.1.x` | SSR/Next.js، Django templates | SPA کوچک و static build با stack مصوب سازگار است. Next.js/SSR نیاز محصول و deployment requirement ایجاد می‌کند و رد شد. patch دقیق هنگام lockfile pin می‌شود. |
| Database | PostgreSQL `18.x` | SQLite، document store | ownership/lifecycle/feedback query و production persistence به relational constraints نیاز دارند. JSONB فقط payloadهای atomic را نگه می‌دارد. |
| Production edge | static gateway/reverse proxy + WSGI Django | Vite preview؛ سرو مستقیم SPA با Django؛ Node SSR | Vite preview production server نیست. gateway کوچک static asset و same-origin `/api` را بدون Node runtime ارائه می‌کند. |
| Guest identity | Django database session + opaque `GuestContext` | JWT/localStorage، account، fingerprint | server-side revocation/expiry و CSRF semantics مستند دارد؛ JWT و fingerprint داده/پیچیدگی بی‌نیاز اضافه می‌کنند. |
| Concurrency | input revision + conditional database update | queue، distributed lock | late result correctness با compare-and-swap حل می‌شود؛ queue/Redis برای first slice لازم نیست. |
| Answers/evidence | schema-versioned JSONB embedded؛ ownership/feedback relational | table per answer/evidence؛ یک JSON document کامل | answerها/evidence همیشه با report atomic خوانده می‌شوند و query تحلیلی مصوب ندارند؛ lifecycle و rating queryable می‌مانند. |
| AI integration | یک provider-neutral protocol + strict validator | provider registry، agent framework | کمترین seam تست‌پذیر را می‌دهد و deterministic domain را جدا می‌کند. real provider تا تصمیم limits deferred است. |

## Official-source findings

- Django download page نسخه current و LTS/support windows را منتشر می‌کند؛ انتخاب LTS تصمیم هزینه نگهداری است، نه
  ادعای performance: <https://www.djangoproject.com/download/>.
- DRF release/support metadata در repository رسمی است: <https://github.com/encode/django-rest-framework/releases>.
- Django session docs database backend، expiry و cleanup با `clearsessions` را شرح می‌دهد:
  <https://docs.djangoproject.com/en/5.2/topics/http/sessions/>.
- DRF authentication docs روشن می‌کند که CSRF در SessionAuthentication فقط برای authenticated request الزام می‌شود
  و anonymous request ممکن است بدون token عبور کند؛ بنابراین guest API به `csrf_protect` استاندارد Django نیاز دارد:
  <https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication>.
- Vite build guide `vite build` و خروجی static را مستند می‌کند و preview را production server نمی‌داند:
  <https://vite.dev/guide/static-deploy.html>.
- PostgreSQL current supported releases از صفحه رسمی versioning/releaseها کنترل می‌شود:
  <https://www.postgresql.org/support/versioning/>.
- Compose healthcheck/readiness dependency در مستند رسمی Docker آمده است:
  <https://docs.docker.com/compose/how-tos/startup-order/>.

نسخه‌ها planning baseline هستند. تنها versionهای واقعاً مشاهده‌شده در workspace در `docs/tooling.md` ثبت‌اند؛ هیچ
application package نصب و benchmark نشده است.

## Frontend skills provenance correction

repository رسمی Vercel Labs در commit
`1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` بررسی شد:
<https://github.com/vercel-labs/agent-skills>.

- tree exact همین commit از GitHub API بررسی شد و هیچ فایل root یا skill-specific با نام `LICENSE`, `NOTICE` یا
  `COPYING` ندارد. `react-best-practices/SKILL.md` فقط metadata `license: MIT` دارد، اما متن grant/notice ندارد؛
  `web-design-guidelines` هیچ declaration مجوزی ندارد. بنابراین گزارش قبلی MIT برای هر دو قابل اتکا نبود.
- از Phase 5 این دو snapshot vendored مبنای guidance تازه نیستند. overlay اصیل پروژه بر مستندات رسمی React، Vite و
  WAI/WCAG تکیه دارد؛ application code Phase 4 حذف یا بازنویسی نشد.
- overlay پروژه باید Persian-first RTL، `lang=fa`, semantic DOM order، keyboard/focus، پیام خطای پول و عدم اتکا به
  رنگ را اضافه کند.

snapshotها برای provenance حفظ شده‌اند ولی inactive محسوب می‌شوند؛ redistribution تا ارائه license روشن مجاز فرض
نمی‌شود. بخش‌های Next.js، RSC/SSR و Vercel همچنان خارج scope هستند.

## Phase 5 provider comparison

| معیار | OpenAI `gpt-6-luna` | Google `gemini-3.5-flash-lite` |
|---|---|---|
| structured output | Responses API JSON Schema؛ پشتیبانی مستند | JSON Schema subset؛ پشتیبانی مستند |
| قیمت Standard / 1M token | input `$0.10`، output `$0.50` | input `$0.30`، output `$2.50` |
| فارسی | multilingual capability مستند؛ کیفیت فارسی اندازه‌گیری نشده | translation/simple processing مستند؛ کیفیت فارسی اندازه‌گیری نشده |
| data handling | API data برای training استفاده نمی‌شود؛ `store=false` application state را غیرفعال می‌کند؛ abuse monitoring عادی تا ۳۰ روز مگر ZDR | paid tier برای بهبود محصول استفاده نمی‌شود؛ free tier استفاده می‌شود |
| region | فقط فهرست رسمی؛ ایران در فهرست نیست | فقط فهرست رسمی و API client در available region؛ ایران در فهرست نیست |
| انتخاب | **مشروط انتخاب شد**؛ ارزان‌تر و contract-compatible | رد اولیه؛ گران‌تر و region blocker را حل نمی‌کند |

منابع رسمی: <https://developers.openai.com/api/docs/models/gpt-6-luna>،
<https://developers.openai.com/api/docs/pricing>،
<https://developers.openai.com/api/docs/guides/structured-outputs>،
<https://developers.openai.com/api/docs/guides/your-data>،
<https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories>،
<https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite>،
<https://ai.google.dev/gemini-api/docs/pricing>،
<https://ai.google.dev/gemini-api/docs/structured-output> و
<https://ai.google.dev/gemini-api/docs/available-regions>.

نتیجه measured فعلی فقط provenance/price/config comparison است؛ call زنده، latency، quality فارسی و cost مشاهده‌شده
هنوز وجود ندارد. dataset و thresholdهای pre-registered در [ai-evaluation.md](ai-evaluation.md) هستند.

## Backend skill evaluation

local catalog مهارت متمرکز Django/DRF نداشت. candidateهای public زیر از نظر scope بررسی شدند:

- `nimadorostkar/Claude-Skills-collection` / Django: پوشش گسترده ORM/migration/DRF دارد، اما به skillهای جدا و scope
  عمومی تکیه می‌کند.
- `Jeffallan/claude-skills` / `django-expert` `1.1.0` (MIT): Django 5.0 و JWT/مهارت‌های وابسته را پیش‌فرض می‌گیرد؛
  با guest session و minimal layering پروژه ناسازگار است.
- `vintasoftware/django-ai-plugins`: guidance گسترده‌تر production/deployment دارد، اما برای slice متمرکز این feature
  بیش از حد وسیع است.

انتخاب: پیش از نخستین backend implementation، candidateها یک‌بار برای تغییرات جدید re-check و سپس یک skill محلی
کوچک بر پایه docs رسمی ساخته می‌شود که فقط validation، permission/ownership، sessions/CSRF، migration، ORM query،
API contract و behavioral test را پوشش دهد. JWT، repository pattern، async stack و framework اضافی ممنوع‌اند.

## Deferred evaluations

- Playwright CLI + skill رسمی در tag `v1.65.1` برای browser verification انتخاب شد؛ automated testها با runner
  هم‌نسخه اجرا می‌شوند و MCP چون capability لازم اضافه‌ای نداشت deferred ماند:
  <https://github.com/microsoft/playwright-mcp>.
- code intelligence فقط پس از vertical slice نماینده و طبق benchmark ثبت‌شده در `docs/tooling.md` بررسی می‌شود.
- live AI activation به supported region، credential و spending authorization وابسته است؛ backup retention و exact
  production sizing همچنان deployment gate هستند.

## Rejected complexity

Redis، Celery، WebSocket، microservice، event sourcing، full report history، analytics SDK، provider registry، JWT،
account system و SSR برای requirement فعلی benefit concrete ندارند و انتخاب نشدند.
