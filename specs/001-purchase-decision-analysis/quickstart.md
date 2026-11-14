# M3 Development Quickstart

M1 backend و M2 رابط React فارسی/RTL پیاده‌اند. مسیر توسعه از Vite proxy هم‌origin به Django/PostgreSQL داخل
Docker وصل می‌شود. adapter live پیاده است ولی پیش‌فرض خاموش و live evaluation pending است؛ production deployment
هنوز اجرا نشده است.

## پیش‌نیاز و نصب قفل‌شده

Python `3.12.x`، uv `0.13.0`، Node `20.19.0`، npm `10.8.2` و Docker/Compose لازم‌اند. نصب قفل‌شده:

```bash
uv sync --frozen
cp .env.example .env
cd frontend && npm ci
```

اگر package host محلی timeout داد، build image همان lockfile را در محیط Linux نصب می‌کند:

```bash
docker compose build api
```

## startup و smoke cookie/CSRF

```bash
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up -d --wait

curl --fail --silent --show-error \
  --cookie-jar /tmp/beforebuy-cookies.txt \
  http://127.0.0.1:58000/api/v1/session

CSRF_TOKEN=$(awk '$6 == "csrftoken" {print $7}' /tmp/beforebuy-cookies.txt)
curl --fail --silent --show-error \
  --cookie /tmp/beforebuy-cookies.txt \
  --cookie-jar /tmp/beforebuy-cookies.txt \
  -H "X-CSRFToken: ${CSRF_TOKEN}" \
  -H 'Content-Type: application/json' \
  --data '{"product_label":"گوشی نمونه","price_toman":"۲۰٬۰۰۰٬۰۰۰","budget_toman":"۲۵٬۰۰۰٬۰۰۰","answers":{"Q-001":"UNUSABLE","Q-002":"RESTORE_ESSENTIAL_ACCESS","Q-003":["GENERAL_USE"],"Q-004":"WITHIN_2_WEEKS","Q-006":["NONE"],"F-003":"NO_INFORMATION"}}' \
  http://127.0.0.1:58000/api/v1/analyses
```

پاسخ باید `201`، `rubric_id=PDA-CAT-v0.3` و `mode=MOCK_ASSISTED` داشته باشد. نبود/خرابی CSRF برابر `403` است.

## رابط توسعه

در terminal جدا:

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

آدرس مرورگر `http://127.0.0.1:5173/` است. hostname را بین startup و browser test عوض نکنید. origin همین Vite
در `.env.example` trusted است؛ CSRF فعال می‌ماند و CORS لازم نیست. پاسخ‌ها/ownership در PostgreSQL و session
سرورند و draft در localStorage/sessionStorage نوشته نمی‌شود.

## verification

```bash
POSTGRES_PORT=55439 .venv/bin/python backend/manage.py check --settings=config.settings.test
POSTGRES_PORT=55439 .venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=config.settings.test

cd backend
POSTGRES_PORT=55439 ../.venv/bin/python manage.py test tests --settings=config.settings.test

cd ../frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run typecheck
npm run lint
npm test
npm run build
PLAYWRIGHT_HTML_OPEN=never npm run test:e2e
```

Playwright `1.65.1` در macOS 12 از Chrome نصب‌شده با channel `chrome` استفاده می‌کند؛ bundled Chromium این host
را پشتیبانی نمی‌کند. browser test به API Docker روی پورت `58000` نیاز دارد. حالت محدود فقط وقتی
`BEFOREBUY_E2E_TEST_CONTROLS=1` و header اختصاصی تست حاضر باشد تزریق می‌شود؛ مقدار نمونه/production برابر `0` است.

Analysis retention از نخستین report برابر ۹۰ روز و non-sliding است. فقط persist موفق یک analysis جدید، access
guest/session را تا expiry همان analysis تازه تمدید می‌کند. read/edit/retry/feedback retention را تمدید نمی‌کنند.
از دست‌رفتن cookie recovery ندارد. برای cleanup و محدودیت‌های عملیاتی، `docs/backend-operations.md` را ببینید.

## فعال‌سازی و ارزیابی live AI

فعال‌سازی عمومی با وجود key به‌تنهایی مجاز نیست. direct OpenAI برای deployment ایران غیرفعال است. فقط پس از پاسخ
مکتوب provider درباره eligibility/upstream و تأیید credit موجود، در `.env` محلی backend این مقادیر را تنظیم کنید:

```dotenv
BEFOREBUY_AI_MODE=live
BEFOREBUY_AI_PROVIDER=avalai
BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=1
AVALAI_API_KEY=<set-locally>
```

برای run هفت‌موردی synthetic evaluation، cap صریح حداکثر ۱۰۰٬۰۰۰ تومان تعیین کنید. command قبل از model call،
credential/eligibility/credit/rate/cap و reservation کامل retryها را کنترل می‌کند و raw prompt/response را persist نمی‌کند:

```bash
BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN=100000 \
docker compose run --rm api python backend/manage.py evaluate_live_ai --artifact-dir artifacts/ai-evaluation
docker compose run --rm api python backend/manage.py assess_ai_review artifacts/ai-evaluation/<run-id>.json
```

خروجی automatic فقط structural/operational evidence است و semantic fields تا review انسانی `null` می‌مانند.
mock test یا summary خودکار جای live/human evidence نیست.
