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

- mode پیش‌فرض `mock` است. direct OpenAI برای deployment ایران غیرفعال است و legacy region flag باید صفر بماند.
  `live` فقط با provider=`avalai`، clarification eligibility، key backend، نرخ تازه و budget تومان انتخاب می‌شود؛
  نبود هر gate به `RULE_BASED_LIMITED` می‌انجامد و rubric قطعی همچنان منتشر می‌شود.
- provider/model/prompt/schema ثابت فعلی: AvalAI Responses API، `gpt-5.6-luna`، `PDA-EXPLAIN-P1` و
  `PDA-EXPLAIN-v1`. SDK موجود `3.49.0` و dependencyها در `uv.lock` پین‌اند؛ Responses support از docs AvalAI است.
- هر generation یک bound محافظه‌کار ۸۱۹۲ token-equivalent برای کل instructions/input/schema/framing margin، ۵۱۲
  output token، timeout هشت ثانیه و دو attempt دارد. فقط connection/timeout/408/409/429/5xx retry می‌شوند.
- `AILiveBudgetWindow` با row lock، worst-case همه attemptها را پیش از call رزرو می‌کند. deployment budget تومان
  و نرخ IRT-per-UNIT بدون default مثبت‌اند و در نبود تنظیم صریح fail closed می‌شوند؛ per-guest برابر ۱۰ generation/day
  است و پنج failure متوالی circuit را پنج دقیقه باز می‌کند.
  provider call بیرون transaction است. settlement idempotent است، usage مشاهده‌شده clip نمی‌شود و retry/usage نامعلوم
  reservation کامل را charge می‌کند. invoice provider مرجع نهایی است و application cap تضمین invoice نیست.
- `AIInvocation` فقط provider/model/version، latency، token usage، attempt count، status/error class، request ID و estimate هزینه
  را نگه می‌دارد. answer، label، session secret، prompt/response یا exception text ذخیره نمی‌شود و metadata متصل به
  guest پس از ۹۰ روز در cleanup حذف می‌شود.
- evaluation cap هیچ default ندارد و با `BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN` فقط برای command صریح و حداکثر
  ۱۰۰٬۰۰۰ تومان تنظیم می‌شود. command قبل از model call نرخ/credit را از User API AvalAI می‌گیرد، margin ۱۵٪ و
  همه retryها را رزرو می‌کند. estimate تضمین invoice نیست.

### آماده‌سازی محلی AvalAI بدون ارسال secret

پیش از تغییر eligibility، از پشتیبانی AvalAI پاسخ مکتوب این سه مورد را بگیرید: مجازبودن کاربرد این محصول برای
backend/کاربر ایران و مسیر upstream؛ محل/مدت نگهداری prompt/output در هر دو لایه؛ و قابل‌مصرف‌بودن signup grant
برای `gpt-5.6-luna` بدون top-up/minimum balance. این repository پیام یا ticket خارجی ارسال نمی‌کند.

پس از دریافت پاسخ و فقط اگر حساب/اعتبار از قبل موجود است، key را در secret environment محلی تنظیم کنید؛ نه در chat،
frontend یا Git. موجودی و نرخ را بدون model call بررسی کنید:

```bash
export AVALAI_API_KEY='<local-secret>'
curl -sS https://api.avalai.ir/user/v1/credit \
  -H "Authorization: Bearer $AVALAI_API_KEY"
```

اگر `remaining_irt` موجود برای reservation کافی و model در credit scope مجاز بود، متغیرهای زیر را فقط در shell/
secret manager قرار دهید. `BEFOREBUY_AI_USD_TO_TOMAN_RATE` برای live application از `exchange_rate` همان پاسخ است؛
evaluation آن را دوباره از User API می‌خواند:

```bash
export BEFOREBUY_AI_MODE=live
export BEFOREBUY_AI_PROVIDER=avalai
export BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=1
export BEFOREBUY_AI_MODEL=gpt-5.6-luna
export BEFOREBUY_AI_USD_TO_TOMAN_RATE='<fresh-exchange_rate>'
export BEFOREBUY_AI_DAILY_BUDGET_TOMAN='<approved-production-cap>'
export BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN=100000
python backend/manage.py evaluate_live_ai --artifact-dir artifacts/ai-evaluation
```

اگر account نیازمند خرید، subscription یا top-up بود، متوقف شوید؛ Phase 5.2 چنین اختیاری نمی‌دهد. پس از run، artifact
فقط synthetic baseline/AI output و metadata را دارد و چهار field human review تا تکمیل reviewer برابر null می‌مانند.

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
