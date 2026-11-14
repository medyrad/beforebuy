# تحویل Phase 6.2 — بستن gapهای محیط توسعه

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline بازبینی‌شده:** `80af259202937bc6c7bf8e69bd4881ee971db24b`  
**وضعیت:** migration دادهٔ development، loopback port binding و فرمان canonical backend تکمیل و محلی verify شدند  
**مرز:** بدون provider call، خرید، deployment عمومی، تغییر production routing یا تکمیل `T039`

## نتیجه و Spec Kit

- taskهای محدود `T062..T065` به feature موجود اضافه شدند؛ `T039` همچنان unchecked است.
- requirement یا plan محصول تغییر نکرد، بنابراین طبق دستور Phase 6.2 اجرای `$speckit-analyze` لازم نبود.
- prerequisite رسمی `$speckit-implement` feature را در
  `/Users/mehdi/Projex/beforebuy/specs/001-purchase-decision-analysis` یافت؛ checklistهای requirements برابر
  `30/30` و technical-plan برابر `25/25` و بدون مورد باز بودند.
- implementation فقط migration توسعه، loopback binding، test wrapper، testهای Compose و مستندات مرتبط را پوشش داد.
  production Compose، AI configuration و frontend تغییر نکردند.

## finding دقیق PostgreSQL development

finding baseline تأیید شد. container اولیه `beforebuy-db-1` از image زیر استفاده می‌کرد:

`postgres@sha256:aa6eb304ddb6dd26df23d05db4e5cb05af8951cda3e0dc57731b771e0ef4ab29`

| بررسی | مقدار مشاهده‌شده پیش از cutover |
|---|---|
| image `PGDATA` | `/var/lib/postgresql/18/docker` |
| image `VOLUME` | `/var/lib/postgresql` |
| runtime `SHOW data_directory` | `/var/lib/postgresql/18/docker` |
| named mount قدیمی | `beforebuy_beforebuy_pgdata -> /var/lib/postgresql/data` |
| محل واقعی داده | anonymous volume `19a94ccdea7cc860ef2d58f4f7c453c7a0ec94dfef01765b57904a36d16e86ba -> /var/lib/postgresql` |
| database / user / owner | هر سه `beforebuy`؛ ownership مبهم نبود |
| migration state | `0001/0002` applied؛ `0003/0004` pending |

restart persistence به‌عنوان مدرک استفاده نشد. mount inspection نشان داد named volume قدیمی `PGDATA` را نمی‌پوشاند
و دادهٔ واقعی در anonymous parent volume بود.

## backup، restore و تطبیق داده

ابتدا API متوقف شد؛ database source تا پایان dump روشن ولی بدون client connection دیگر بود. backup نهایی custom-format
در مسیر خارج repository ساخته شد:

```text
/Users/mehdi/Backups/beforebuy/phase-6.2-20261115/beforebuy-development-pre-cutover.dump
SHA-256: 76f733b802ef1e62ac482e8d6781a7b0d5ef00b745078bf5aa341edfbba7a4f4
directory mode: 0700
dump mode: 0600
```

`pg_restore --list` archive را خواند. dump در **named volume تازه**
`beforebuy_beforebuy_pgdata_v18` و همان image digest restore شد. سپس migrationهای `0003` و `0004` فقط روی مقصد
اعمال و `migrate --check` بدون migration pending اجرا شد. source anonymous volume، named volume قدیمی و backup حذف یا
تغییر داده نشدند.

مقایسهٔ source و destination بدون نمایش محتوای رکورد:

| evidence | source | destination پس از restore/migrate |
|---|---:|---:|
| guest context | 154 | 154 |
| analysis | 29 | 29 |
| current report | 29 | 29 |
| feedback | 0 | 0 |
| Django session | 154 | 154 |
| live budget window | 0 | 0 |
| AI invocation | 0 | 0 |
| evaluation authorization | table هنوز موجود نبود | 0 پس از migration |
| ownership/FK orphan | 0 | 0 |
| decoded owner session / missing owner | `154 / 0` | `154 / 0` |
| ownership digest | `720b8cdc0c9eefdcf1cf48d2744a0434` | همان |
| session digest | `e1037e32a62d969e3416bf7646263a41` | همان |

accounting source خالی بود؛ در نتیجه authorization یا spending موجودی برای reset وجود نداشت و migration نیز allowance
جدیدی نساخت. هیچ evaluation spending authorization تغییر یا ایجاد نشد.

## cutover، recreation و port evidence

`compose.yaml` اکنون volume صریح `beforebuy_beforebuy_pgdata_v18` را روی `/var/lib/postgresql` mount می‌کند و
portهای قابل‌تنظیم را به این شکل منتشر می‌کند:

- PostgreSQL: `127.0.0.1:${POSTGRES_HOST_PORT:-55439}:5432`
- API: `127.0.0.1:${API_HOST_PORT:-58000}:8000`

container موقت restore متوقف و حذف شد؛ سپس source DB متوقف و stack با `docker compose up -d --force-recreate --wait`
بازسازی شد. هیچ `down --volumes` یا حذف volume اجرا نشد. runtime پس از cutover:

- mount فقط `beforebuy_beforebuy_pgdata_v18 -> /var/lib/postgresql` و anonymous mount صفر؛
- `SHOW data_directory=/var/lib/postgresql/18/docker`؛
- published bindings دقیقاً `127.0.0.1:55439` و `127.0.0.1:58000`؛
- readiness API در `http://127.0.0.1:58000/api/v1/health/ready` برابر `200` و `{"status":"ready"}`.

برای اثبات persistence مستقل از container، DB و API یک بار دیگر با `--force-recreate` ساخته شدند. هر دو container ID
عوض شدند، اما countها، ownership digest و session digest ثابت ماندند؛ mount همچنان named parent volume بود و
readiness دوباره `200` شد.

## reconciliation تست‌های backend

فرمان canonical از ریشه repository:

```bash
scripts/test-backend.sh
```

wrapper از working directory `backend/` و label `tests` استفاده می‌کند؛ در نتیجه package ریشهٔ `tests/e2e` وارد
discovery Django نمی‌شود. روی macOS مسیر Docker Desktop CLI را در صورت وجود به `PATH` اضافه می‌کند.

گزارش قدیمی `128 discovered, 125 passed, 1 skipped` اشتباه جمع ساده نبود. identifier دقیق skip:

```text
setUpClass (tests.test_production_compose.ProductionComposeTests)
reason: Docker CLI is required to render production Compose
```

این class سه test method داشت. هر سه در discovery برابر ۳ محسوب شدند، اما `SkipTest` در `setUpClass` فقط یک skip event
ثبت کرد؛ بنابراین `128 - 3 = 125` method اجرا شد و یک class-level skip گزارش شد. «دو test باقی‌مانده» missing،
deselected یا error نبودند؛ تفاوت حساب ناشی از جایگزین‌شدن سه method کشف‌شده با یک skip event بود.

اجرای تازه با wrapper و `-v 2`:

| discovered | run | passed | skipped | failed | errors |
|---:|---:|---:|---:|---:|---:|
| 130 | 130 | 130 | 0 | 0 | 0 |

افزایش ۱۲۸ به ۱۳۰ فقط دو test جدید development Compose است. هر سه test production Compose این بار واقعاً اجرا و
پاس شدند؛ بنابراین skipped identifier در اجرای canonical تازه وجود ندارد. testهای جدید ابتدا روی mount قدیمی و
bind بدون `host_ip` هر دو RED شدند، سپس پس از اصلاح هر دو GREEN شدند.

## rollback

مواد rollback عمداً نگه‌داری می‌شوند:

- source واقعی و untouched:
  `19a94ccdea7cc860ef2d58f4f7c453c7a0ec94dfef01765b57904a36d16e86ba`؛
- named volume قدیمی و untouched: `beforebuy_beforebuy_pgdata`؛
- dump محافظت‌شده و checksum بالا؛
- destination فعال: `beforebuy_beforebuy_pgdata_v18`.

برای rollback ابتدا `docker compose stop api db` اجرا شود. روی source یا destination فعال restore نکنید. dump را در
یک named volume تازه با همان image digest restore، migration و fingerprintها را verify و سپس آن volume تازه را با
override محلی Compose فعال کنید. source anonymous volume schema قبل از `0003/0004` دارد و نباید با code جاری مستقیم
فعال شود. هیچ‌گاه `docker compose down --volumes` اجرا نکنید و backup را به Trash منتقل نکنید.

## فایل‌ها و gateهای باقی‌مانده

- `T039`: live AvalAI evidence هفت case و human semantic review کامل؛ همچنان unchecked.
- clarification مکتوب provider دربارهٔ eligibility/upstream/data retention و credit بدون خرید.
- target-host certificate/secret واقعی، host cleanup schedule activation، monitoring و تصمیم صریح public release.
- live AI call در این phase: صفر؛ provider cost: صفر.
- deletion نامرتبط `test.txt` preserve و از commit Phase 6.2 خارج می‌شود.

**Development PostgreSQL migrated to the verified PostgreSQL 18 named-volume layout; live AI and public release remain pending.**
