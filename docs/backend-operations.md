# عملیات backend و بستهٔ production تا M4

`compose.yaml` فقط stack توسعه است. بستهٔ production در `compose.production.yaml` سه service `web → api → db`
دارد؛ تکمیل rehearsal محلی به‌معنای مجوز انتشار عمومی یا آمادگی live AI نیست.

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
  provider call بیرون transaction است. settlement idempotent است؛ usage معلوم هر attempt کامل جمع می‌شود و هر
  attempt نامعلوم فقط allowance محافظه‌کارانهٔ خودش را می‌گیرد. overage clip نمی‌شود و reserved underflow خطای
  integrity است. invoice provider مرجع نهایی است و application cap تضمین invoice نیست.
- `AIEvaluationAuthorization` allowance اولیهٔ ۱۰۰٬۰۰۰ تومان را مستقل از deployment window نگه می‌دارد. spent و
  outstanding reservation در restart، process هم‌زمان و UTC-midnight reset نمی‌شوند؛ midnight فقط window روزانه را
  عوض می‌کند. هر reserve هر دو scope را atomically بررسی می‌کند.
- `AIInvocation` فقط metadata عملیاتی sanitized شامل run/case/operation، provider/model/version، usage معلوم/نامعلوم،
  request ID و snapshot نرخ را نگه می‌دارد. حذف guest آن را فوراً cascade نمی‌کند تا evidence/reconciliation باقی بماند؛
  cleanup ۹۰روزه همچنان آن را حذف می‌کند. answer، label، secret، raw prompt/response و exception text ذخیره نمی‌شود.
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

command پیش از call و بعد از هر case artifact را با replace اتمیک checkpoint می‌کند. rejection بودجه/guest/circuit
به‌صورت `status=rejected`، attempts/model-call صفر و reason ساختاریافته ثبت می‌شود و run موفق نیست. برای resume:

```bash
python backend/manage.py evaluate_live_ai \
  --resume-artifact artifacts/ai-evaluation/<run-id>.json
```

اگر checkpoint دارای invocation رزروشدهٔ ناتمام باشد، resume آن reservation را محافظه‌کارانه recover/settle،
`recovered_failed` و سپس case را با operation تازه اجرا می‌کند. این recovery تخمین ایمن است؛ مبلغ provider/invoice
نامعلوم را مبلغ قطعی معرفی نمی‌کند. پیش از reconcile دستی rowهای `reserved` را حذف یا counterها را ویرایش نکنید.

اگر account نیازمند خرید، subscription یا top-up بود، متوقف شوید؛ Phase 5.2 چنین اختیاری نمی‌دهد. پس از run، artifact
فقط synthetic baseline/AI output و metadata را دارد و چهار field human review تا تکمیل reviewer برابر null می‌مانند.

## بستهٔ production و startup کنترل‌شده

فایل `deploy/production.env.example` را به یک مسیر خارج Git کپی کنید و path مطلق certificate، key و دو secret file
با permission محدود را تنظیم کنید. `DJANGO_ALLOWED_HOSTS` و `DJANGO_CSRF_TRUSTED_ORIGINS` باید صریح باشند و origin
فقط HTTPS است. `web` تنها port منتشرشده است؛ API/DB فقط روی networkهای Compose هستند. gateway مقدار
`X-Forwarded-Proto=https` را جایگزین می‌کند و API فقط از network داخلی به آن دسترس دارد؛ همین مرز اعتماد دلیل
`SECURE_PROXY_SSL_HEADER` است.

```bash
docker compose --project-name beforebuy-prod \
  --env-file /etc/beforebuy/production.env -f compose.production.yaml config --quiet
docker compose --project-name beforebuy-prod \
  --env-file /etc/beforebuy/production.env -f compose.production.yaml build
docker compose --project-name beforebuy-prod \
  --env-file /etc/beforebuy/production.env -f compose.production.yaml up -d --wait db
docker compose --project-name beforebuy-prod \
  --env-file /etc/beforebuy/production.env -f compose.production.yaml run --rm api \
  python backend/manage.py migrate --noinput
docker compose --project-name beforebuy-prod \
  --env-file /etc/beforebuy/production.env -f compose.production.yaml up -d --wait
```

migration عمداً command جداست و در CMD یا workerهای Gunicorn اجرا نمی‌شود. `DEBUG` و test control در production رد
می‌شوند؛ secret key، hosts و origins غایب startup را متوقف می‌کنند. rehearsal با `BEFOREBUY_AI_MODE=mock` انجام می‌شود
و UI آن را «نسخهٔ نمایشی / هوش مصنوعی زنده نیست» نشان می‌دهد. live ناقص نیز هنگام import تنظیمات production fail می‌شود.

## retention cleanup

```bash
docker compose run --rm api python backend/manage.py purge_expired_analyses
```

این فرمان analysisهای منقضی، AI invocationهای قدیمی‌تر از ۹۰ روز، GuestContext منقضیِ بدون analysis و sessionهای منقضی Django را حذف می‌کند. دسترسی
در query از لحظهٔ expiry بسته است؛ purge فقط حذف فیزیکی active storage است. پیش از production باید همین فرمان حداقل
روزانه با host scheduler اجرا می‌شود تا target حداکثر ۲۴ ساعت رعایت شود. واحدهای نمونه در `deploy/systemd/` هر روز
ساعت ۰۲:۱۵ UTC `deploy/run-maintenance.sh` را اجرا می‌کنند؛ این script ابتدا backup و سپس cleanup را اجرا می‌کند.

```bash
sudo install -m 0644 deploy/systemd/beforebuy-maintenance.service /etc/systemd/system/
sudo install -m 0644 deploy/systemd/beforebuy-maintenance.timer /etc/systemd/system/
sudo systemd-analyze verify /etc/systemd/system/beforebuy-maintenance.{service,timer}
sudo systemctl daemon-reload
sudo systemctl enable --now beforebuy-maintenance.timer
systemctl list-timers beforebuy-maintenance.timer
journalctl -u beforebuy-maintenance.service
```

وجود command به‌تنهایی کافی نیست؛ operator باید `list-timers` و آخرین exit موفق journal را در host مقصد ببیند.
rehearsal محلی macOS یک launchd job موقت را دو بار اجرا کرد و آخرین exit آن صفر بود؛ job بلافاصله unload شد. activation
systemd روی host Linux عمومی همچنان بخشی از release checklist است. Celery/Redis لازم نیست.

## backup، restore و حذف

pilot پیش‌فرض یک `pg_dump --format=custom` روزانه و نگهداری rolling هفت‌روزه است. `deploy/backup-postgres.sh`
فایل‌های قدیمی‌تر از شش روز کامل را پس از backup موفق حذف می‌کند. directory و فایل‌ها باید فقط برای operator قابل
خواندن باشند، filesystem/volume میزبان باید encrypted at rest باشد و هر نسخهٔ off-host پیش از انتقال با کلید خارج
repository رمز شود. dump، certificate، private key و runtime log وارد Git نمی‌شوند.

```bash
export BEFOREBUY_COMPOSE_PROJECT=beforebuy-prod
export BEFOREBUY_PRODUCTION_ENV=/etc/beforebuy/production.env
export BEFOREBUY_BACKUP_DIR=/var/backups/beforebuy
deploy/backup-postgres.sh
```

restore همیشه در project و volume خالی جدا انجام می‌شود؛ هرگز روی volume فعال restore نکنید:

```bash
export BEFOREBUY_COMPOSE_PROJECT=beforebuy-restore-incident
export BEFOREBUY_PRODUCTION_ENV=/etc/beforebuy/restore.env
export BEFOREBUY_RESTORE_DUMP=/var/backups/beforebuy/<chosen>.dump
deploy/restore-postgres.sh
docker compose --project-name "$BEFOREBUY_COMPOSE_PROJECT" \
  --env-file "$BEFOREBUY_PRODUCTION_ENV" -f compose.production.yaml run --rm api \
  python backend/manage.py purge_expired_analyses
```

پیش از بازکردن restored app: live AI را خاموش نگه دارید؛ expiry cleanup را اجرا کنید؛ `AIEvaluationAuthorization`،
reservation و spent را با صورتحساب/ledger اصلی reconcile کنید؛ و سپس ownership/session را با دادهٔ synthetic یا
incident checklist بررسی کنید. restore مجاز نیست allowance را reset کند یا هزینهٔ قبلی را دوباره قابل‌مصرف کند.

حذف active storage فوری است، اما dumpهای retained می‌توانند داده‌ای را که بعداً حذف شده نگه دارند. این برنامه deletion
event log ندارد؛ بنابراین recovery کوچک و fail-closed است: restore در شبکه ایزوله می‌ماند، cleanup اجرا می‌شود، همه
درخواست‌های حذف شناخته‌شده پس از timestamp backup از ثبت عملیاتی incident دوباره اعمال می‌شوند، و اگر فهرست کامل
قابل بازسازی نباشد restored instance برای کاربران باز نمی‌شود. پس از هفت روز backup چرخه عادی حذف می‌شود؛ erasure
فوری نسخه‌های backup ادعا نمی‌شود.

## migration و rollback

پیش از migration روی database غیرخالی backup بگیرید. ابتدا fresh database و سپس schema قبلی مشخص را تمرین کنید.
application rollback فقط به image digest قبلی که با schema جاری سازگار و قبلاً health/browser-tested است انجام می‌شود:

```bash
API_IMAGE=registry.example/beforebuy-api@sha256:<tested-compatible-digest> \
docker compose --project-name beforebuy-prod --env-file /etc/beforebuy/production.env \
  -f compose.production.yaml up -d --no-deps --wait api
```

اگر migration با image قبلی ناسازگار است، app rollback کافی نیست: traffic بسته می‌ماند و database از backup قبل migration
در volume تازه restore می‌شود. migration دلخواه reversible فرض نمی‌شود و production database هیچ‌گاه با `migrate <old>`
به‌صورت آزمایشی عقب برده نمی‌شود.

## محدودیت‌های فعلی

- live adapter وجود دارد ولی evaluation واقعی و کیفیت فارسی/latency آن تا فراهم‌شدن gateها اندازه‌گیری نشده است.
- cookie از دست‌رفته یا منقضی recovery و cross-device access ندارد.
- `check --deploy` باید با `config.settings.production` و secretهای runtime اجرا شود؛ TLS در gateway خاتمه می‌یابد.
- logging پیکربندی‌شده answer، session/CSRF و raw AI payload را ثبت نمی‌کند.
