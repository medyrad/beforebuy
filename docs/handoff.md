# تحویل Phase 6.1 — اصلاح و اثبات production configuration

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline بازبینی‌شده:** `bf5f6cc8ee0a6407ca851f274dee692d5c00efd6`  
**وضعیت:** اصلاحات production configuration پیاده و در rehearsal محلی ایزوله verified شد؛ live AI و انتشار عمومی pending  
**مرز:** بدون deployment عمومی، provider/paid call، خرید اعتبار، تغییر M3 یا تکمیل T039

## نتیجه و Spec Kit

- requirementهای corrective با `FR-051..FR-053` و `SC-010..SC-012` و taskهای `T058..T061` به feature موجود اضافه شدند.
- `$speckit-analyze` پس از prerequisite رسمی اجرا شد: ۶۵ requirement/criterion و ۶۱ task، بدون duplicate ID،
  placeholder، constitution conflict یا finding بحرانی/high. یک نکتهٔ low فقط نام دقیق overlay بود که به
  `compose.production.live.yaml` حل شد.
- `$speckit-implement` فقط `T058..T061` را با red/green اجرا کرد. هر چهار task کامل‌اند؛ `T039` باز است.
- checklistهای Spec Kit بدون تغییر reviewer state برابر requirements `30/30` و technical-plan `25/25` باقی ماندند.
- handoff Phase 6 در `docs/archive/phase-6-handoff.md` آرشیو شد.

## finding PostgreSQL و اصلاح volume

finding baseline تأیید شد. image دقیق production:

`postgres:18.1-alpine@sha256:aa6eb304ddb6dd26df23d05db4e5cb05af8951cda3e0dc57731b771e0ef4ab29`

| بررسی | مقدار مشاهده‌شده |
|---|---|
| image RepoDigest | `postgres@sha256:aa6eb304ddb6dd26df23d05db4e5cb05af8951cda3e0dc57731b771e0ef4ab29` |
| image `PGDATA` | `/var/lib/postgresql/18/docker` |
| image `VOLUME` | `/var/lib/postgresql` |
| runtime `SHOW data_directory` | `/var/lib/postgresql/18/docker` |
| named-volume destination پس از اصلاح | `/var/lib/postgresql` |
| mount DB | فقط `volume beforebuy-m61_postgres_data /var/lib/postgresql`؛ secret bind جدا؛ anonymous volume صفر |

mount قبلی production روی `/var/lib/postgresql/data`، `PGDATA` واقعی را نمی‌پوشاند. `compose.production.yaml` به
layout رسمی PostgreSQL 18 اصلاح شد. مستند رسمی image نیز تغییر 18+ به version-specific `PGDATA` و parent volume را
تأیید می‌کند: <https://github.com/docker-library/docs/blob/master/postgres/content.md#pgdata>.

برای حفاظت داده، پیش از تغییر config همهٔ volume/containerهای موجود inspect شدند. project production قبلی وجود نداشت.
container توسعهٔ موجود همان اشکال را نشان داد: named volume قدیمی روی `/var/lib/postgresql/data` و anonymous parent
volume روی `/var/lib/postgresql`؛ `SHOW data_directory` نیز مسیر 18 را داد. از database توسعه dump ایمنی custom-format
گرفته شد و هیچ volume توسعه حذف، reinitialize یا remount نشد. تغییر توسعه به‌علت نیاز به migration داده، خارج scope
production Phase 6.1 ماند و در operations به‌عنوان gap جدا ثبت شد.

## آزمون recreation و persistence

rehearsal با project مستقل `beforebuy-m61`، HTTPS port `58445` و named volume
`beforebuy-m61_postgres_data` انجام شد. داده‌ها کاملاً synthetic بودند:

- یک analysis و current report در mode mock؛
- session مالک browser و feedback برابر ۵؛
- `AIEvaluationAuthorization`: authorized=`100000`، reserved=`7000`، spent=`23000` تومان؛
- `AILiveBudgetWindow`: reserved=`111` و spent=`222` microusd؛
- یک `AIInvocation` با provider=`synthetic` و attempt صفر.

`docker compose down` بدون `--volumes` هر سه container و network را حذف کرد. همان named volume با labelهای
`project=beforebuy-m61` و `volume=postgres_data` باقی ماند و stack از production config دوباره ساخته شد. پس از recreate:

- `data_directory` همان `/var/lib/postgresql/18/docker` و mount همان named volume بود؛
- countها analysis=`1`، session=`2`، feedback=`1` و invocation=`1` باقی ماندند؛
- accounting دقیقاً `100000/7000/23000` و `111/222` باقی ماند؛
- Playwright با storage state مالک، analysis و rating ۵ را دوباره خواند: `1 passed`؛
- health پس از recreate برابر `200` بود.

بنابراین evidence به restart وابسته نیست و persistence به anonymous volume متکی نیست.

پس از جمع‌آوری evidence، container/networkهای rehearsal بدون `--volumes` متوقف و حذف شدند. volume اصلی synthetic
و volume خالی live-config check عمداً حذف نشدند؛ certificate، dump، cookie، storage state و secretهای runtime از
workspace خارج و به‌صورت recoverable به Trash محلی منتقل شدند و هیچ‌کدام وارد Git نمی‌شوند.

## production AI configuration

`compose.production.yaml` اکنون همهٔ non-secretهای factory را صریح map می‌کند: mode، provider، model، AvalAI
eligibility، timeout، attempts، input/output limits، guest quota، deployment budget، USD→toman rate، margin و circuit
threshold/cooldown. `BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED` و `BEFOREBUY_E2E_TEST_CONTROLS` در production صفرند.

- base production default برابر mock است و بدون AvalAI secret healthy شد؛ settings واقعی container:
  provider=`avalai`، model=`gpt-5.6-luna`، eligible=false، key_present=false، budget/rate=`0` و test_controls=false.
- اجرای live بدون overlay/config کامل با exit=`1` و پیام actionable برای eligibility، file credential، budget و rate رد شد.
- `compose.production.live.yaml` فقط در live، file secret را به `/run/secrets/avalai_api_key` mount می‌کند.
- credential کاملاً synthetic با overlay و factory transport stub بارگذاری شد: `loaded_from_file=true`،
  `stub_selected=true`، provider calls=`0` و test controls=false.
- test rendering واقعی با `docker compose --env-file ... config --format json` ثابت کرد marker موجود فقط در host
  env-file وارد container نمی‌شود، اما متغیرهای صریح map‌شده مقدار درست می‌گیرند.

هیچ AvalAI/OpenAI call، token، usage یا هزینه‌ای در این Phase وجود نداشت.

## health host، proxy و CSRF

healthcheck دیگر `Host: localhost` ثابت نمی‌فرستد و از `BEFOREBUY_HEALTHCHECK_HOST` استفاده می‌کند. production settings
خالی‌بودن، نبودن در `DJANGO_ALLOWED_HOSTS` و wildcard را fail closed رد می‌کند.

در runtime با host مصنوعی `rehearsal.beforebuy.test`:

- readiness با Host allowlisted برابر `200`؛
- Host نامعتبر برابر `400`؛
- `X-Forwarded-Proto=https` و secure redirect/proxy setting حفظ شد؛
- cookieهای CSRF و session دارای `Secure` و `SameSite=Lax` بودند و session نیز `HttpOnly` بود؛
- POST same-origin بدون CSRF token برابر `403`؛ flow معتبر CSRF در regressionهای backend پاس شد.

هیچ wildcard host، خاموش‌کردن validation یا تغییر gateway trust boundary انجام نشد.

## verification اجراشده

| فرمان/بررسی | نتیجه |
|---|---|
| focused production settings/Host tests | ۱۰/۱۰ پاس روی PostgreSQL |
| rendered Compose behavior tests | ۳/۳ پاس |
| backend canonical suite از `backend/` با dev venv | ۱۲۵ پاس، ۱ skip؛ ۱۲۸ test discovered |
| Django system check | issue صفر |
| `makemigrations --check --dry-run` | `No changes detected` |
| Playwright seed قبل recreation | ۱ پاس |
| Playwright owner read بعد recreation | ۱ پاس |
| production image build و سه service `up --wait` | موفق و هر سه healthy |
| provider activity | صفر call و صفر هزینه |

دو اجرای نامعتبر evidence محسوب نشدند: اجرای host اولیه با port/password نادرست پیش از اتصال test DB متوقف شد؛ اجرای
suite در image production به‌علت نبود dev-only `PyYAML` شش import error داشت. dependency توسعه به image production
اضافه نشد و suite canonical با venv توسعه اجرا و پاس شد. `manage.py test` از repo root نیز به‌علت collision `tests/e2e`
صفر test کشف می‌کند؛ working directory معتبر `backend/` است.

## gateهای باقی‌مانده

- `T039`: live AvalAI evidence هفت case و review انسانی کامل؛ همچنان unchecked.
- clarification مکتوب provider دربارهٔ eligibility/upstream/data retention و credit بدون خرید.
- target-host certificate/secret واقعی، systemd activation، monitoring و تصمیم صریح public deployment.
- migration امن volume توسعهٔ موجود از anonymous PostgreSQL 18 parent به named volume؛ production اصلاح شده است.
- هیچ full-product convergence یا public/live readiness ادعا نمی‌شود.

**Production configuration gaps corrected and locally verified; live AI and public release pending**
