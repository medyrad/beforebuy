# عملیات backend تا M3

این سند فقط stack توسعهٔ Django/PostgreSQL را پوشش می‌دهد. production gateway، TLS، backup/restore و deployment
در M4 هستند و این Compose production-ready نیست.

## راه‌اندازی

```bash
cp .env.example .env
docker compose build api
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up -d --wait
curl --fail http://127.0.0.1:58000/api/v1/session
```

پورت‌های پیش‌فرض میزبان `58000` برای API و `55439` برای PostgreSQL هستند و با `API_HOST_PORT` و
`POSTGRES_HOST_PORT` تغییر می‌کنند. API از Django development server استفاده می‌کند؛ این انتخاب فقط برای توسعه است.

## تست و migration

```bash
POSTGRES_PORT=55439 .venv/bin/python backend/manage.py check --settings=config.settings.test
POSTGRES_PORT=55439 .venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=config.settings.test
cd backend
POSTGRES_PORT=55439 ../.venv/bin/python manage.py test tests --settings=config.settings.test
```

پس از اضافه‌شدن `tests/e2e` در M2، test label باید از working directory `backend/` اجرا شود تا با namespace ریشه
تداخل نکند. اجرای `manage.py test tests` از ریشه اکنون عمداً command معتبر suite backend محسوب نمی‌شود.
race testها به PostgreSQL واقعی متصل‌اند و از `threading.Event` استفاده می‌کنند، نه sleep.

## live AI و کنترل هزینه

- mode پیش‌فرض `mock` است. `live` فقط با تأیید صریح region و key محیط backend انتخاب می‌شود؛ نبود هر gate به
  `RULE_BASED_LIMITED` می‌انجامد و rubric قطعی همچنان منتشر می‌شود.
- provider/model/prompt/schema ثابت فعلی: OpenAI Responses API، `gpt-6-luna`، `PDA-EXPLAIN-P1` و
  `PDA-EXPLAIN-v1`. SDK `3.49.0` و dependencyها در `uv.lock` پین‌اند.
- هر generation حداکثر ۸۱۹۲ byte ورودی (upper-bound محافظه‌کار token)، ۵۱۲ output token، timeout هشت ثانیه و دو
  attempt دارد. فقط connection/timeout/408/409/429/5xx retry می‌شوند.
- `AILiveBudgetWindow` با row lock، worst-case همه attemptها را پیش از call رزرو می‌کند. default deployment cap
  برابر `$1/day` و per-guest برابر ۱۰ generation/day است؛ پنج failure متوالی circuit را پنج دقیقه باز می‌کند.
  provider call بیرون transaction است. invoice provider مرجع نهایی است و هزینهٔ ذخیره‌شده estimate بر پایه pricing
  ثبت‌شده است.
- `AIInvocation` فقط provider/model/version، latency، token usage، attempt count، status/error class و estimate هزینه
  را نگه می‌دارد. answer، label، session secret، prompt/response یا exception text ذخیره نمی‌شود و metadata متصل به
  guest پس از ۹۰ روز در cleanup حذف می‌شود.
- evaluation cap هیچ default ندارد و با `BEFOREBUY_LIVE_EVAL_BUDGET_USD` فقط برای command صریح تنظیم می‌شود.

## retention cleanup

```bash
docker compose run --rm api python backend/manage.py purge_expired_analyses
```

این فرمان analysisهای منقضی، AI invocationهای قدیمی‌تر از ۹۰ روز، GuestContext منقضیِ بدون analysis و sessionهای منقضی Django را حذف می‌کند. دسترسی
در query از لحظهٔ expiry بسته است؛ purge فقط حذف فیزیکی active storage است. پیش از production باید همین فرمان حداقل
روزانه با cron یا systemd timer اجرا شود تا target حداکثر ۲۴ ساعت رعایت شود. Celery/Redis لازم نیست. lifecycle و
حذف backup هنوز در M4 تعیین می‌شود.

## محدودیت‌های فعلی

- live adapter وجود دارد ولی evaluation واقعی و کیفیت فارسی/latency آن تا فراهم‌شدن gateها اندازه‌گیری نشده است.
- cookie از دست‌رفته یا منقضی recovery و cross-device access ندارد.
- `check --deploy` روی development settings هشدارهای طبیعی DEBUG/HTTP می‌دهد؛ hardening تولید در M4 است.
- logging پیکربندی‌شده answer، session/CSRF و raw AI payload را ثبت نمی‌کند.
