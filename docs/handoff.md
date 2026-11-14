# تحویل Phase 6 — بستهٔ production و rehearsal ایزوله M4

**تاریخ:** ۱۴ نوامبر ۲۰۲۶  
**baseline:** `be5f21e79a949cfe07a9c8732781c752577fda66`  
**وضعیت:** بستهٔ production محلی rehearse شد؛ live AI و انتشار عمومی pending  
**مرز:** بدون deployment عمومی، خرید infrastructure، provider call یا تغییر M3

## نتیجه و Spec Kit

- dependency اصلاح شد: packaging readiness در T041–T043 مستقل از T039 قابل تکمیل است؛ public-release readiness به هر
  دو جریان evidence نیاز دارد.
- `$speckit-analyze` پس از prerequisite رسمی و checklistهای 30/30 و 25/25 اجرا شد؛ conflict بحرانی یا constitution
  violation نداشت. gap متوسط این بود که معیارهای عملیاتی M4 بیشتر در plan/task هستند تا FR مستقل؛ scope صریح T041–T043
  اجرا شد و convergence دوباره این موضوع را گزارش می‌کند.
- `$speckit-implement` فقط T041–T043 را اجرا کرد. T039 باز، live call صفر و public release بسته ماند.
- `$speckit-converge` پس از implementation اجرا شد: gap تازهٔ M4 نداشت؛ یک finding `partial/high` همان live/human
  evidence ناتمام `T039` بود. task تازه append نشد چون T039 دقیقاً مالک همان کار است؛ نتیجه عمداً `Converged` اعلام نشد.
- handoff Phase 5.3 بدون تغییر در `docs/archive/phase-5.3-handoff.md` آرشیو شد.

## بستهٔ سه‌سرویسی و امنیت

`compose.production.yaml` دقیقاً `web → api → db` دارد:

- `web`: build چندمرحله‌ای Node `24.11.0-alpine3.22` از `npm ci`، asset استاتیک Vite و runtime غیرroot
  NGINX unprivileged `1.30.6`. مسیر `/api/` same-origin proxy و سایر مسیرها SPA fallback هستند؛ Vite server وجود ندارد.
- `api`: Python `3.12.12-slim` + uv `0.13.0` و `uv sync --frozen --no-dev`، Gunicorn `23.0.0` و user غیرroot
  `beforebuy`. migration در worker startup نیست.
- `db`: PostgreSQL official `18.1-alpine` با volume صریح و init رسمی؛ user آن دستکاری نشده است.
- فقط `127.0.0.1:58443 → web:8443` منتشر شد. inspection واقعی API را فقط `8000/tcp` داخلی و DB را بدون host port
  نشان داد. network DB داخلی است.
- secretهای Django/PostgreSQL از file mount خوانده می‌شوند؛ certificate/key/secret/dump در `.runtime/` ignored بودند.
  نبود pathهای لازم Compose config را fail کرد. production settings نیز secret/host/origin اجباری، DEBUG=false،
  secure cookie، HTTPS-only trusted origin و proxy trust boundary صریح دارد.
- `DJANGO_DEBUG=1`، `BEFOREBUY_E2E_TEST_CONTROLS=1` و live config ناقص fail-closed شدند. rehearsal فقط mock بود و UI
  «نسخهٔ نمایشی / هوش مصنوعی زنده نیست» را نشان داد.
- `check --deploy` پس از افزودن clickjacking middleware و HTTPS redirect فقط دو warning آگاهانه برای HSTS
  includeSubDomains/preload دارد؛ این دو تا تعیین domain عمومی فعال نمی‌شوند تا subdomain ناشناخته قفل نشود.

## فرمان startup و URL

```bash
docker compose --project-name beforebuy-m4 \
  --env-file /absolute/path/production.env -f compose.production.yaml build
docker compose --project-name beforebuy-m4 \
  --env-file /absolute/path/production.env -f compose.production.yaml up -d --wait db
docker compose --project-name beforebuy-m4 \
  --env-file /absolute/path/production.env -f compose.production.yaml run --rm api \
  python backend/manage.py migrate --noinput
docker compose --project-name beforebuy-m4 \
  --env-file /absolute/path/production.env -f compose.production.yaml up -d --wait
```

URL rehearsal: `https://localhost:58443/`. فایل نمونه فقط non-secret config در `deploy/production.env.example` است.

## evidence اجراشده

| بررسی | نتیجهٔ مشاهده‌شده |
|---|---|
| production settings + health tests | ۶/۶ پاس روی PostgreSQL |
| image build | API و web موفق؛ frontend `vite build`، ۲۴ module و assetهای static |
| health/readiness | db، api و web healthy؛ `/healthz` و `/api/v1/health/ready` برابر 200 |
| HTTPS/static/direct route | root و `/?view=history` از asset buildشده؛ secure-cookie/CSRF فعال |
| browser smoke | Playwright/Chrome: create، read، edit، feedback، direct report URL، reload/history و delete؛ ۱ پاس |
| port isolation | فقط web loopback published؛ API/DB host port ندارند |
| restart persistence | هر سه container restart؛ session مالک، analysis و rating دوباره خوانده شدند؛ ۱ پاس |
| missing/forbidden config | Compose بدون TLS path fail؛ secret غایب، DEBUG/test switch و live ناقص fail |
| provider activity | `BEFOREBUY_AI_MODE=mock`؛ live invocation/call/token/cost همگی صفر |
| regression | backend `121 passed`؛ frontend `8 passed`؛ typecheck/lint/build پاس؛ runtime `npm audit --omit=dev` صفر vulnerability |

دو finding در rehearsal با evidence اصلاح شدند: health probe ابتدا Host غیرمجاز `127.0.0.1` می‌فرستاد و به headerهای
trusted اصلاح شد؛ NGINX ابتدا `root` صریح نداشت و fallback loop می‌ساخت، سپس direct route پاس شد. نخستین browser command
به Node ناسازگار Hermes خورد؛ با Node قفل‌شدهٔ موجود `20.19.0` و بدون تغییر dependency اجرا شد.

## backup، restore، expiry و accounting

- `deploy/backup-postgres.sh` یک dump custom-format با umask 077 ساخت و retention هفت‌روزه را اعمال کرد. maintenance
  بعدی نیز backup تازه و cleanup موفق ساخت.
- dump واقعی در project دوم `beforebuy-m4-restore` و volume خالی restore شد. پیش از بازکردن web/API،
  `purge_expired_analyses` اجرا شد: حذف‌ها صفر بودند.
- restored data شامل یک analysis synthetic، GuestContext/session مالک و feedback=5 بود. همان storage state مرورگر روی
  `https://localhost:58444` analysis و rating را خواند؛ browser check پاس شد.
- authorization مصنوعی `authorized=100000`، `reserved=7000` و `spent=23000` تومان بدون reset restore شد. live mode
  پس از restore همچنان mock ماند؛ re-spend مجاز نشد.
- پس از backup، analysis در source حذف شد؛ نسخهٔ restored همچنان آن را داشت. این عمداً ثابت کرد backup درخواست حذف
  بعدی را بازسازی نمی‌کند. procedure fail-closed در operations می‌گوید restore ایزوله، cleanup، reapply درخواست‌های
  حذف شناخته‌شده و در نبود فهرست کامل «عدم بازگشایی»؛ event sourcing اضافه نشده است.
- backupهای retained ممکن است دادهٔ حذف‌شده داشته باشند؛ erasure فوری backup ادعا نمی‌شود. storage باید restricted و
  encrypted at rest و نسخهٔ off-host پیش از انتقال رمز شود.

## migration، rollback و schedule

- fresh database از صفر تا migration `0004` کامل شد.
- project سوم روی schema `0003` ساخته شد؛ backup قبل migration گرفته و سپس `0004` + dependencyها اعمال شد. چهار migration
  analysis همگی `[X]` شدند.
- application rollback مکانیکی به image ID سازگار و تست‌شده
  `sha256:ccd6e29bf211395c8e2b4812865cef0bb1a9a4a3e982a19fe7268bdc8d4cf57c` انجام و readiness 200 شد. این evidence
  rollback به image/schema مشخص است؛ rollback arbitrary migration ادعا نمی‌شود. migration ناسازگار باید با restore
  backup قبل migration در volume تازه recovery شود.
- maintenance payload واقعی backup+cleanup را موفق اجرا کرد. validation timer در container Debian به‌علت pull شبکه
  کامل نشد؛ به‌جای ادعای pass، host scheduler macOS با launchd job موقت واقعی اجرا شد: دو run، آخرین exit=0 و cleanup
  log موفق؛ job سپس unload شد. unit/timer production systemd ثبت است و activation/`list-timers` روی host Linux مقصد
  همچنان release checklist است.

## policy هزینهٔ اصلاح‌شده

`512 × $30/M = $0.01536` فقط سهم output در worst-case reservation است، نه observed average. این bound ریسک عبور از
target تاریخی `$0.0025/generation` را نشان می‌دهد، اما به‌تنهایی ناممکن‌بودن average را ثابت نمی‌کند. target تغییر
نکرد؛ observed cost/generation تا live evidence برابر unmeasured، product-cost gate و overall pass برابر null و total
evaluation allowance مستقل ۱۰۰٬۰۰۰ تومان باقی ماند.

## gateهای باقی‌مانده

- T039: live AvalAI evidence هفت case و review انسانی کامل.
- clarification مکتوب provider دربارهٔ eligibility/upstream/data retention و credit بدون خرید.
- هیچ credential/credit محلی مجاز، provider call یا artifact انسانی در این Phase وجود نداشت.
- target-host systemd activation، certificate/secret واقعی، monitoring و تصمیم صریح public deployment.
- public deployment و ادعای full-product readiness مجاز یا انجام‌شده نیست.

## وضعیت taskها

- T041: کامل و verified.
- T042: کامل و verified.
- T043: کامل برای rehearsal محلی ایزوله؛ target-host scheduler/public rollout یک release gate جدا و pending است.
- T039: باز.

**Production package locally rehearsed; live AI and public release pending**
