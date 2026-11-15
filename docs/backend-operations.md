# عملیات backend و بستهٔ production تا M4

## Credential mount recovery — 2026-11-16

The running API had only `/app`, no `/run/secrets/copilot_master_keyring`; `keyring()` was unavailable.
The original mode-0600 `/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key` remained intact.
Recreated API with the existing secret overlay, without database recreation, migrations, rotation or real-key changes:

```sh
export COPILOT_MASTER_KEYRING_PATH=/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key
bash scripts/dev-with-credentials.sh up -d --no-deps api
# Use this same wrapper for future Compose starts to retain the secret mount.
```

The wrapper refuses missing, relative or unreadable paths before invoking Docker. It does not generate keys.
Canonical full startup: `COPILOT_MASTER_KEYRING_PATH=/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key bash scripts/dev-with-credentials.sh up -d`.
Final delivery re-ran it with `--no-deps --force-recreate api`; mount and encryption availability remained present.
No-secret offline startup was checked with a disposable `docker compose run --rm --no-deps` API process,
`COPILOT_MASTER_KEY_FILE=` and mock/OFFLINE, running Django `check` successfully. No database reset or volume deletion.
Runtime `keyring()` now succeeds; `COPILOT_AI_MODE=mock`, `BEFOREBUY_RESEARCH_MODE=OFFLINE`.
Frontend rebuild/recreation uses `build web`, then `up -d --no-deps web` through the wrapper.
No secret contents printed or embedded; existing volumes and credentials are preserved. Browser verification uses
fresh guest contexts with disposable synthetic credentials only. Do not collect traces/screenshots of key entry.

Free-provider integration is pending; see `specs/002-personalized-shopping-copilot/free-provider-readiness.md`.

## Bounded UX redesign — local operation and rollback (2026-11-16)

- Default `/` and compatible `/copilot` serve the new conversation UI. `/legacy`, `/?analysis=<id>` and
  `/?view=history` preserve feature001; API routing/ownership is unchanged. Both NGINX configurations already use
  SPA `try_files`; no public routing, wildcard hosts or production security changes are needed.
- Keep `COPILOT_AI_MODE=mock` and `BEFOREBUY_RESEARCH_MODE=OFFLINE`. Read-only settings now expose credential_state
  separately from regional connection block and effective mode. Do not replace the existing `.env`, keyring,
  encrypted OpenAI credential or selected provider to exercise the UX. No validation button is needed for local chat.
- First message creates a conversation. Category/recipient choices and explicit money statements use the normal
  owner/CSRF/message/idempotency/worker path. Conflicting budget is a proposal until confirmed; reply actions are
  stale after a newer turn/revision. Clear history preserves credentials/settings/accounting and cascades derived memory.
- Migration `0017_conversational_ux` adds two JSON fields only. Before applying it, application writes were stopped
  with `docker compose stop api`; a protected custom-format logical backup was created and `pg_restore --list`
  successfully read its listing (241 lines). This is archive readability, not a new full restore rehearsal.

```text
/Users/mehdi/Backups/beforebuy/ux-redesign-7fUJFR/pre-ux.dump
directory 0700; dump 0600; 276705 bytes
SHA-256 41f9d49f10167083af29c46b059aec16fffd48689f86a1274879d230ac082b6a
```

Keep this backup out of Git and Trash. Existing `beforebuy_beforebuy_pgdata_v18` and all other volumes remain intact.
Migration applied via `docker compose run --rm --no-deps api python backend/manage.py migrate --noinput`.
Rebuild/recreate only API/web as needed, without `down --volumes`. Existing runtime data is not a test fixture.
UX rollback: serve the prior frontend image/route while retaining additive schema/data. Database rollback requires
a new isolated destination volume, explicit restore validation and reconciliation of deletions/accounting; never
restore over the active development volume. Public target-host, live-provider/source and human evaluation gates remain.

Canonical focused UX verification (from repository root, installed compatible Node on PATH):

```sh
./scripts/test-backend.sh --keepdb --verbosity 1
node frontend/node_modules/vitest/vitest.mjs run --root frontend --maxWorkers=1
NODE_PATH="$PWD/frontend/node_modules" COPILOT_SCREENSHOT_DIR="$PWD/artifacts/screenshots" PLAYWRIGHT_BASE_URL=http://127.0.0.1:58080 node frontend/node_modules/@playwright/test/cli.js test --config frontend/playwright.config.ts tests/e2e/copilot-ux-redesign.spec.ts tests/e2e/copilot-choice-desk.spec.ts --reporter=list
```

Browser tests bootstrap isolated guests through actual NGINX and use synthetic records. A bounded client-delivery
delay makes stream switching/stop reproducible; it is not a provider-latency measurement. Physical mobile keyboards,
real device zoom and live model quality need separate validation. Exact results/screenshots are recorded in handoff.

`compose.yaml` فقط stack توسعه است. بستهٔ production در `compose.production.yaml` سه service `web → api → db`
دارد؛ تکمیل rehearsal محلی به‌معنای مجوز انتشار عمومی یا آمادگی live AI نیست.

## Phase 9.3 — local research diagnostics

No AI token is required. From repository root, inspect one reviewed Torob URL with fresh, proxy-free connections:

```sh
uv run python scripts/diagnose-research.py --layer direct
uv run python scripts/diagnose-research.py --layer safe
docker compose exec -T api python scripts/diagnose-research.py --layer direct
docker compose exec -T api python scripts/diagnose-research.py --layer safe
```

Direct records DNS/family/TCP/TLS/HTTP; safe runs the actual SafeFetcher/extractor. No body/cookie/credential is printed
or retained. Phase 9.3 charges 12/30 attempts (10 inspected + 2 conservative reservations). Do not rerun indefinitely.
The following single pilot invocation reserves at most 16 attempts (4 preflight + at most 6 per one-target API job).
It submits zero API jobs unless preflight extracts offers, then creates two fresh conversations to avoid cache reuse.
Its successful branch has **not** been executed; only the failed-preflight stop was verified. After success, verify
PostgreSQL and the offer journey at `http://127.0.0.1:58080/copilot`; browser research also consumes the remaining cap.
Another network is not assumed to resolve HTTP 490. No machine is provisioned or deployed.

```sh
docker compose exec -T api python backend/manage.py configure_market_sources --enable
BEFOREBUY_RESEARCH_MODE=LIVE docker compose up -d --no-build --force-recreate api
docker compose exec -T api python scripts/pilot-reviewed-offer.py
```

Always restore explicitly after success or failure:

```sh
docker compose exec -T api python backend/manage.py configure_market_sources --disable
BEFOREBUY_RESEARCH_MODE=OFFLINE docker compose up -d --no-build --force-recreate api
docker compose exec -T api python backend/manage.py shell -c 'from django.conf import settings; from analysis.models import SourcePolicy; print(settings.BEFOREBUY_RESEARCH_MODE, SourcePolicy.objects.filter(live_enabled=True).count())'
```

Expected effective output: `OFFLINE 0`. Toggles preserve observation timestamps/readiness. Exact timestamps created by
the old command are configuration evidence, not new review; consult the dated source register. Regression command:
`./scripts/test-backend.sh --keepdb --verbosity 1`.

## راه‌اندازی

```bash
cp .env.example .env
docker compose build api
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up -d --wait
curl --fail http://127.0.0.1:58000/api/v1/session
```

پورت‌های پیش‌فرض میزبان `58000` برای API و `55439` برای PostgreSQL هستند و با `API_HOST_PORT` و
`POSTGRES_HOST_PORT` تغییر می‌کنند. هر دو port در development Compose صریحاً فقط روی `127.0.0.1` bind می‌شوند.
API از Django development server استفاده می‌کند؛ این انتخاب فقط برای توسعه است.

## تست و migration

```bash
POSTGRES_PORT=55439 .venv/bin/python backend/manage.py check --settings=config.settings.test
POSTGRES_PORT=55439 .venv/bin/python backend/manage.py makemigrations --check --dry-run --settings=config.settings.test
scripts/test-backend.sh
```

wrapper از ریشه به `backend/` می‌رود، environment توسعه را بدون تغییر label بارگذاری و فقط `backend/tests` را با
`config.settings.test` اجرا می‌کند. این command با namespace ریشهٔ `tests/e2e` تداخل ندارد. در macOS، اگر Docker
Desktop نصب باشد، مسیر CLI آن را به `PATH` اضافه می‌کند تا testهای rendered Compose به‌جای class-level skip اجرا شوند.
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
با permission محدود را تنظیم کنید. `DJANGO_ALLOWED_HOSTS`، `DJANGO_CSRF_TRUSTED_ORIGINS` و
`BEFOREBUY_HEALTHCHECK_HOST` باید صریح باشند؛ health host باید دقیقاً عضو allowlist و بدون wildcard باشد و origin
فقط HTTPS است. `web` تنها port منتشرشده است؛ API/DB فقط روی networkهای Compose هستند. gateway مقدار
`X-Forwarded-Proto=https` را جایگزین می‌کند و API فقط از network داخلی به آن دسترس دارد؛ همین مرز اعتماد دلیل
`SECURE_PROXY_SSL_HEADER` است.

PostgreSQL production روی digest دقیق
`postgres@sha256:aa6eb304ddb6dd26df23d05db4e5cb05af8951cda3e0dc57731b771e0ef4ab29` است. metadata همین image
`PGDATA=/var/lib/postgresql/18/docker` و `VOLUME=/var/lib/postgresql` دارد؛ بنابراین named volume باید روی
`/var/lib/postgresql` mount شود، نه `/var/lib/postgresql/data`. پس از هر تغییر image major، هر سه مقدار image
metadata، `SHOW data_directory` و `docker inspect <db> --format '{{json .Mounts}}'` را دوباره تطبیق دهید. restart
مدرک کافی نیست؛ containerها باید با `down` بدون `--volumes` حذف و از همان named volume بازسازی شوند. هیچ volume
فعال را برای این بررسی delete یا reinitialize نکنید.

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

`--env-file` فقط برای interpolation خود Compose است و همهٔ کلیدهای آن خودکار وارد container نمی‌شوند. متغیرهای
non-secret AvalAI در `compose.production.yaml` صریح map شده‌اند: mode، provider، model، eligibility، timeout، attempt،
input/output limits، guest quota، deployment budget، USD→toman rate، margin و circuit controls. direct-OpenAI region
flag در Compose همیشه صفر و test controls همیشه خاموش‌اند. mock default به AvalAI secret نیاز ندارد.

برای live، پس از بسته‌شدن gateهای provider/credential/credit و بدون قرار دادن key در env یا Git، overlay را اضافه کنید:

```bash
docker compose --project-name beforebuy-prod \
  --env-file /etc/beforebuy/production.env \
  -f compose.production.yaml -f compose.production.live.yaml config --quiet
docker compose --project-name beforebuy-prod \
  --env-file /etc/beforebuy/production.env \
  -f compose.production.yaml -f compose.production.live.yaml up -d --wait
```

در فایل خارج Git مقدار `AVALAI_API_KEY_FILE_PATH=/absolute/restricted/path` را تنظیم کنید. overlay آن را فقط به
`/run/secrets/avalai_api_key` mount و `AVALAI_API_KEY_FILE` را به همان path اشاره می‌دهد. production settings هم
provider/model/eligibility/credential، تمام limitها، rate/margin، budget و circuit values را fail closed بررسی می‌کند.
وجود این wiring مجوز فعال‌سازی live یا provider call نیست.

## retention cleanup

```bash
docker compose run --rm api python backend/manage.py purge_expired_analyses
```

این فرمان analysisهای منقضی، conversationهای منقضی Milestone A، bytesهای upload و stream eventهای منقضی،
AI invocationهای قدیمی‌تر از ۹۰ روز، GuestContext منقضیِ بدون analysis/conversation فعال و sessionهای منقضی Django
را حذف می‌کند. Uploadهای Milestone A در PostgreSQL volume محافظت‌شده نگه‌داری می‌شوند؛ static/public media URL ندارند
و فقط endpoint مالک bytes بازکدگذاری‌شده را می‌دهد. دسترسی در query از لحظهٔ expiry بسته است؛ purge فقط حذف فیزیکی
active storage است. پیش از production باید همین فرمان حداقل
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

## stack توسعهٔ کامل Milestone A

پس از بازبینی `.env`، migration را جدا و بدون reset volume اجرا کنید و سپس stack offline را بالا بیاورید:

```bash
docker compose up -d db
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up --build -d --wait
```

رابط جدید در `http://127.0.0.1:58080/copilot` و feature 001 در `http://127.0.0.1:58080/` است. NGINX مسیر SSE را
با buffering/cache/gzip خاموش و read timeout محدود عبور می‌دهد؛ Gunicorn با دو process از نوع `gthread` و چهار
request thread در هر process اجرا می‌شود. admission صریح فقط دو subscriber SSE را در هر process می‌پذیرد و overflow
را با `429 STREAM_CAPACITY_REACHED` رد می‌کند؛ بنابراین دو thread برای status/cancel باقی می‌ماند و صرف thread count
به‌عنوان admission control تلقی نمی‌شود. هر connection حداکثر 45 ثانیه باز است، heartbeat حداکثر هر 15 ثانیه می‌آید
و reconnect از آخرین event بدون اجرای دوباره انجام می‌شود. disconnect/close slot را idempotent آزاد می‌کند.

`next_sequence - 1` بالاترین sequence صادرشده است. replay آینده با `INVALID_REPLAY_SEQUENCE` و history ناقص یا کاملاً
purgeشده با `REPLAY_GAP` و REST reconciliation URL پاسخ می‌گیرد. purge پس از شروع response یک `stream.replay_gap`
غیرپایدار می‌فرستد و client از operation REST reconcile می‌کند. executor fixture دو worker و queue چهار‌تایی per
process دارد و durable نیست: submit failure به `FAILED/SUBMISSION_FAILED` و restart/lease expiry به `INTERRUPTED`
می‌رسد؛ هیچ‌کدام خودکار از نو اجرا نمی‌شوند. final message، final event، completion event و `COMPLETED` در یک transaction
با lock order `Conversation → StreamOperation` commit می‌شوند. این تنظیم فقط تکمیل Milestone A است؛ T043 و production
rehearsal کامل همچنان بازند.

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

### Phase 10 — local Choice Desk

Migration `0010_shoppingbrief_comparison_choiceset` adds the conversation-local comparison profile and immutable
ChoiceSet rows. Apply it before restarting the updated API; the development PostgreSQL volume is reused, never reset.
Default mode stays OFFLINE/mock with all public policies disabled. Choice comparison and explicit synthetic-demo loading
make no network/provider calls and do not extend conversation retention. ChoiceSets cascade on conversation deletion.

Startup and three worked category demonstrations: `specs/002-personalized-shopping-copilot/quickstart.md`.
`/choices` requires a confirmed revision; edit/expiry/epoch changes invalidate prior results. Empty GET is JSON `null`.
The frontend keeps the existing real-offer panel under «پژوهش منابع و پیشنهادهای فروش», collapsed initially; opening it
does not execute research. Sources/LLM remain independent release gates; this is not Milestone D or live coverage.

Do not reverse 0010 casually: it drops ChoiceSet data and the comparison profile. A rollback needs a protected logical
backup and coordinated code/schema steps; reverting only application code is not promised schema-compatible.
No rollback/reset/volume deletion was performed in this phase. Dedicated migration-test databases are synthetic and
separate from development; no backup or developer database is removed by the verification commands.

### پایلوت منبع واقعی Phase 9.2

حالت امن Compose همچنان `BEFOREBUY_RESEARCH_MODE=OFFLINE` است. policyهای exact-product فقط با فرمان operator نصب
می‌شوند؛ search/account/cart pathها allowlist نیستند:

```bash
docker compose exec api python backend/manage.py configure_market_sources --enable
BEFOREBUY_RESEARCH_MODE=LIVE docker compose up --build -d api web
```

هر job حداکثر سه domain، ۲۰ request، دو redirect/request، ۲MiB wire/decoded/page و ۶۰ ثانیه deadline دارد؛ policyهای
پایلوت pace حداقل ۲ ثانیه و freshness شش ساعت دارند. Phase ceiling عملیاتی جداگانه ۱۰۰ request است و operator باید
مصرف across jobs/diagnostics را ثبت کند. در اجرای 2026-11-15 مصرف کنترل‌شده 29 بود؛ direct pinned access این workspace
به Torob/Technolife/Takkalaban timeout و DNS Bkalaa fail شد. proxy، SSRF bypass یا fixture fallback مجاز نیست.

پس از rehearsal policyها و runtime را به default برگردانید:

```bash
docker compose exec api python backend/manage.py configure_market_sources --disable
docker compose up -d --force-recreate api
```

### volume توسعه و rollback Phase 6.2

PostgreSQL توسعه با image دقیق `postgres@sha256:aa6eb304ddb6dd26df23d05db4e5cb05af8951cda3e0dc57731b771e0ef4ab29`
اجرا می‌شود. `PGDATA=/var/lib/postgresql/18/docker` است؛ بنابراین Compose اکنون named volume
`beforebuy_beforebuy_pgdata_v18` را روی `/var/lib/postgresql` mount می‌کند. source پیش از migration، anonymous volume
`19a94ccdea7cc860ef2d58f4f7c453c7a0ec94dfef01765b57904a36d16e86ba` بود؛ named volume قدیمی
`beforebuy_beforebuy_pgdata` نیز حذف نشده است.

backup قبل cutover در مسیر محدود محلی زیر نگه‌داری می‌شود و نباید commit، منتقل به Trash یا حذف شود:

```text
/Users/mehdi/Backups/beforebuy/phase-6.2-20261115/beforebuy-development-pre-cutover.dump
SHA-256: 76f733b802ef1e62ac482e8d6781a7b0d5ef00b745078bf5aa341edfbba7a4f4
```

directory با mode `0700` و dump با `0600` ساخته شده‌اند. rollback باید ابتدا writeها را با
`docker compose stop api db` متوقف کند. source volume قدیمی را migrate یا overwrite نکنید. برای recovery، dump را
در **یک named volume تازه** با همین image digest restore، `migrate --check` و fingerprintهای ownership/session/accounting
را بررسی و سپس نام volume جدید را در یک override محلی Compose جایگزین کنید. هرگز روی volume فعال restore نکنید و
`docker compose down --volumes` اجرا نکنید. source anonymous volume فقط fallback read-only/forensic است؛ چون schema آن
پیش از migrationهای `0003/0004` است، با code جاری به‌عنوان database فعال استفاده نمی‌شود.

در cutover ثبت‌شده، source دارای ۱۵۴ guest/session، ۲۹ analysis/report، feedback صفر و accounting row صفر بود؛
orphan صفر و همهٔ ۱۵۴ session به owner موجود decode شدند. نبود accounting row یعنی authorization قابل reset وجود
نداشت؛ migration هیچ allowance تازه‌ای ایجاد نکرد. restore مقصد همان countها و digestها را حفظ کرد، چهار migration
را اعمال کرد و پس از recreation containerها نیز بدون anonymous volume ثابت ماند.

- live adapter وجود دارد ولی evaluation واقعی و کیفیت فارسی/latency آن تا فراهم‌شدن gateها اندازه‌گیری نشده است.
- cookie از دست‌رفته یا منقضی recovery و cross-device access ندارد.
- `check --deploy` باید با `config.settings.production` و secretهای runtime اجرا شود؛ TLS در gateway خاتمه می‌یابد.
- logging پیکربندی‌شده answer، session/CSRF و raw AI payload را ثبت نمی‌کند.
- انتشار عمومی همچنان نیازمند certificate/secret واقعی target host، activation زمان‌بندی‌شده cleanup، monitoring و
  تصمیم صریح release است؛ migration توسعه هیچ‌یک از این gateها یا `T039` را تغییر نمی‌دهد.

## Phase 11.1 — contextual assistant operations

`StreamOperation.context_manifest` only stores IDs, revisions, hashes and expiry anchors; user/profile/source prose and
credentials remain ephemeral. The worker pins the latest accepted turn, brief/generation, CopilotSettings revision,
current ChoiceSet/snapshots, eligible uploads and included confirmed-memory revisions. Every delta/final publication
reassembles the context and terminalizes stale work as `CONTEXT_STALE`. Migration `0015` is additive.

Context limits are `COPILOT_CONTEXT_HISTORY_BYTES=6000`, `COPILOT_CONTEXT_CRITICAL_BYTES=32768` and
`COPILOT_CONTEXT_TOTAL_BYTES=49152`. Optional history is truncated deterministically. If critical context cannot fit,
the local limited generator returns before any provider transport. Do not raise these limits without revisiting request
cost, image bounds, SSE payload size and disclosure.

`POST /api/v1/copilot/models/refresh` is the only model-list action. It first enforces region eligibility and a validated
credential, then uses the installed SDK `client.models.list()` and intersects IDs with the documentation catalog.
Settings/credential GET/PUT never discover models. In the confirmed Iran deployment the endpoint returns
`REGION_BLOCKED` before credential decryption or transport; do not use a base URL or UI flag to bypass this.

Development mock output is labelled synthetic and uses the production context assembler, typed plan validator, event
ledger and publication boundary. `PROVISIONAL_CONTEXT` deltas contain only a safe lead; `VALIDATED_BLOCK` deltas are
server-rendered from current deterministic values. Raw Responses JSON is never emitted. Live AI and research remain
disabled; no restart, migration or fixture demonstration authorizes a provider/source call.
# Phase 11 local settings and memory

Default remains `COPILOT_AI_MODE=mock` and `BEFOREBUY_RESEARCH_MODE=OFFLINE`. No real API key is required to explore
`http://127.0.0.1:58080/copilot`. The top navigation exposes «تنظیمات دستیار» and «شناخت من». Saving credentials is
local encrypted storage only: no validation, discovery or provider request. Direct OpenAI remains region-blocked.

For local **synthetic** credential controls, create a protected directory outside the repository and a new keyring:

```sh
uv run python backend/manage.py create_copilot_keyring /absolute/private/path/copilot.key
export COPILOT_MASTER_KEYRING_PATH=/absolute/private/path/copilot.key
docker compose -f compose.yaml -f compose.copilot-secrets.yaml up -d --no-build api web
```

The creation command requires an existing parent, refuses paths inside the repository and never overwrites a file.
Use parent mode 0700 and keyring mode 0600; verify runtime read permission without printing the content. The optional
overlay mounts `/run/secrets/copilot_master_keyring`. On this Docker Desktop host the non-root API UID 100 could read
the protected file. Do not assume identical Linux bind-mount ownership: provision ownership for the deployed runtime
user without making the secret world-readable. Default Compose starts without any master; writes then return 503.

Current restricted local keyring: `/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key`.
It is not an OpenAI credential. Never put either kind of key in Vite variables, Git, logs or screenshots.

Rotation: provision the new master first in the keyring, retain old masters on following lines, run
`python backend/manage.py rotate_copilot_credentials` inside the API runtime, verify successful rewrapping, then
retire old masters only after backup/restore compatibility review. Expiry and credential revisions are not extended.
Lost master without a secure backup means stored API credentials cannot be recovered; users must replace them.
Replace/delete cancels dependent queued/running operations, but cannot recall a provider request already transmitted.
Historical backups are not instantly erased. Browser/session loss has no cross-browser credential/memory recovery.

Non-secret settings: `COPILOT_MEMORY_CANDIDATE_DAYS=7`, `COPILOT_MEMORY_CONFIRMED_DAYS=90`,
`COPILOT_CREDENTIAL_DAYS=30`; these are provisional development defaults, not approved public retention.
`COPILOT_OPERATION_CAP_MICROUSD`, `COPILOT_SESSION_CAP_MICROUSD`, `COPILOT_DAILY_CAP_MICROUSD` default to zero and
must be positive before any future live use; neither nonzero values nor keys bypass eligibility. Development Compose
passes its existing `.env` into the API container. A future production activation requires explicit production wiring
and eligibility review; this phase does not activate it. Do not reset spending aggregates during credential rotation,
memory deletion, purge or backup restoration. Account for retained estimates before authorizing future requests.

Candidate/confirmed memory expiry is non-sliding and bounded by owner/source expiry. Disable stops proposals and
reuse; delete/clear removes active rows. Source conversation deletion cascades derived memory. Explicitly reused
preferences become independent destination brief data with an application receipt. Export is owner-scoped memory
only, not the broader T050 export. Existing expiry command removes expired records; public scheduler remains a gate.

## Phase 12 — GapGPT operational boundary

Migration `0016` adds provider/model selection, a provider-bound encrypted credential row and the provider pinned to
each live operation. Existing `UserCredential` ciphertext is not copied, reinterpreted or deleted. Default execution
remains `COPILOT_AI_MODE=mock`; default research remains `OFFLINE`. The selected exact model uses only fixed
`https://api.gapgpt.app/v1/chat/completions`; Responses, JSON Schema, tools and image input are not claimed.

Local encrypted storage continues to use `compose.copilot-secrets.yaml`. Enter a GapGPT key only in the same-origin
settings UI. GET/PUT/DELETE settings and credentials are zero-call. The explicit model-check action is the only
validation action; after a newly approved spending envelope it makes one bounded generation and records it in the AI
ledger. Success validates only that provider/key/model revision. Key replacement/deletion invalidates queued/running
dependent work; a transmitted request cannot be recalled.

All of these are required before that action or live messages: `COPILOT_PHASE12_SPENDING_AUTHORIZED=1`, a positive
dated `COPILOT_USD_TO_TOMAN_RATE`, positive `COPILOT_PHASE12_TOTAL_CAP_TOMAN`, positive operation/session/daily
micro-USD caps and non-negative `COPILOT_EXCHANGE_MARGIN_RATIO`. The 50,000-toman envelope in provider readiness is
only proposed. The authorization ledger accounts validation plus generation plus retries and reserves unknown-usage
attempts conservatively. Do not reuse the historical 100,000-toman AvalAI evaluation authorization.

Production Compose maps these non-secrets explicitly and keeps all defaults zero/off. The provider key is guest-owned
encrypted database data and the master remains the existing file secret; neither belongs in Compose interpolation,
images, Git or frontend bundles. No Phase 12 provider call, token use, invoice, Persian-quality or latency measurement
exists yet.

## Phase 11 storage recovery and migration evidence

After space recovery, Docker `_ping` returned OK with 7.0 GiB free. Existing `beforebuy-db-1` was started, not
reinitialized. PostgreSQL completed normal crash recovery/checkpoint and accepted connections; no manual filesystem
repair, reset, volume deletion or evaluation-authorization reset was performed. Named volume remains
`beforebuy_beforebuy_pgdata_v18` mounted at `/var/lib/postgresql`. New write errors were not observed in the checked
post-start DB log interval. This is not a forensic certification of every historical row.

Before development migrations, the API was stopped and a custom-format logical backup was created:

```text
/Users/mehdi/Backups/beforebuy/phase-11-20261115/pre-memory-credentials.dump
mode 0600; parent 0700; 200133 bytes
SHA-256 3833d10d45612a82bc5a328498bfbd9af54070e31bdbb997cc8ee7bc2a29f7c2
```

`pg_restore --list` succeeded (217 lines). This confirms archive readability, not a full restoration rehearsal.
Migrations 0011–0014 applied successfully; `makemigrations --check --dry-run` reported no changes. A separately named
fresh test database applied all migrations and passed 22 focused tests before the runner removed only that test DB.
Keep the backup outside Git and out of Trash. Rollback: stop application writes, retain current/source volumes and
restore into a **new** named volume using the documented restore procedure; review accounting before opening access.
Do not assume reverting application code alone reverses schema or restores cryptographic keys. Full production
restoration/release rehearsal remains Milestone E, not completed by this phase.
