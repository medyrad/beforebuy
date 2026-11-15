# Quickstart — Milestone A/B/C offline and fixture stack

## Phase 10 — Choice Desk without tokens or public sources

از root، با `.env` محلی موجود و `BEFOREBUY_AI_MODE=mock`، policyهای عمومی غیرفعال بمانند:

```sh
docker compose up -d db
docker compose run --rm --no-deps api python backend/manage.py migrate --noinput
BEFOREBUY_RESEARCH_MODE=OFFLINE docker compose up -d --build api web
```

`http://127.0.0.1:58080/copilot` را باز کنید؛ «گفت‌وگوی تازه»، در موبایل «میز انتخاب»، سپس «ویرایش brief».
مخاطب و بودجه را تعیین کنید؛ category دقیق `electronics`، `home` یا `sports` و ترجیحات اختیاری را وارد کنید.
«ذخیره» و «تأیید brief برای پژوهش»؛ زیر «محصول موردنظر و جایگزین‌ها» دستهٔ همان نمونه را انتخاب و
«بارگذاری دادهٔ مصنوعی» را بزنید. محصول موردنظر و حداکثر سه جایگزین قابل تغییرند؛ سپس «ساخت مقایسه».
این دکمه هیچ source یا AI call ندارد. قیمت‌ها ساختگی‌اند، نه بازار زنده. برای category دیگر گفت‌وگوی تازه بسازید.

نمونه‌های تکرارپذیر (همه synthetic، همه مبالغ تومان):

| دسته/هدف | نیاز صریح | نتیجهٔ مورد انتظار |
|---|---|---|
| electronics / ENJOYMENT، SELF | سقف ۱۰ میلیون، portable=true شرط قطعی | آ ۸ میلیون و پ ۹ میلیون tie؛ ب ۷ میلیون portable=false و ارسال نامعلوم ناسازگار؛ با سقف ۸ میلیون آ تنها سازگار |
| home / HOUSEHOLD | سقف ۶ میلیون، dishwasher_safe=true شرط قطعی | آ ۶ میلیون سازگار؛ ب ۴ میلیون شرط را نقض می‌کند؛ پ ۷ میلیون بالای سقف و شاهد شست‌وشو/ارسال نامعلوم |
| sports / GIFT | سقف ۲ میلیون، size_eu=42 برای RECIPIENT | آ ۲ میلیون سازگار؛ ب سایز۴۰ ناسازگار؛ پ سایز۴۲ با قیمت۱٫۸ میلیون و ارسال نامعلوم حل‌نشده |

همان criterionها در حالت PRACTICAL نیز بدون داوری دربارهٔ هدف خرید اجرا می‌شوند. unknown shipping یا mandatory fee
هرگز صفر فرض نمی‌شود. کشوی «شواهد و منابع» و disclosure پیشنهادهای فروش، provenance و زمان‌ها را نشان می‌دهند.
تغییر brief نتیجهٔ قبلی را باطل می‌کند؛ تأیید مجدد و ساخت مقایسه لازم است. ریشهٔ `/` همچنان legacy است.

تست backend: `./scripts/test-backend.sh --keepdb --verbosity 1`؛ frontend: `npm --prefix frontend test`،
`npm --prefix frontend run typecheck`، `npm --prefix frontend run lint`، `npm --prefix frontend run build`.
Playwright از image محلی موجود و test واقعی `tests/e2e/copilot-choice-desk.spec.ts` پشت NGINX استفاده می‌کند؛
`PLAYWRIGHT_BASE_URL=http://127.0.0.1:58080`، `PLAYWRIGHT_USE_BUNDLED=1` و `NODE_PATH=/app/frontend/node_modules`.

فرمان‌های LIVE تاریخی زیر، جزو مجوز Phase 10 نیستند؛ default OFFLINE را تغییر ندهید.

Phase 9.3 diagnostics/pilot/reset commands: [backend operations](../../docs/backend-operations.md#phase-93--local-research-diagnostics).
The diagnostic scripts need no AI token. Current source preflight returns HTTP 490; successful live pilot is pending.
Reset with explicit `BEFOREBUY_RESEARCH_MODE=OFFLINE`, never an ambient default.

1. After reviewing `.env`, run `docker compose up -d db`, then `docker compose run --rm api python backend/manage.py
   migrate --noinput`, then `docker compose up --build -d`. Compose builds React, starts Django/PostgreSQL and exposes
   the complete offline stack through NGINX; no host npm process is required and no volume is reset.
2. Open `http://127.0.0.1:58080/copilot`. The legacy feature remains at `/` and direct refresh of `/copilot` uses the
   SPA fallback.
3. Create a conversation, explicitly edit/confirm its brief, send a message and observe real fixture deltas through
   NGINX. The UI must display «حالت توسعه / fixture» and must not show invented products, prices or citations.
4. Stop an active operation, reconnect, and verify REST reconciliation. GET/SSE never start or restart work. A service
   restart may terminalize an in-flight fixture as `INTERRUPTED`; it never silently resumes. Each SSE connection is
   bounded to 45 seconds and reconnects from its last event. Missing retained history or a purge race reconciles with
   `GET /api/v1/operations/{id}` instead of re-running the fixture. Only two subscribers per process are admitted so
   status/cancel requests retain request-thread capacity.
5. Upload at most three JPEG/PNG/WebP images, each ≤5 MiB, ≤4096px per side and ≤12MP. Bytes are decoded/re-encoded,
   metadata removed, stored in PostgreSQL, owner-authorized and expired within 24h.
6. Run the canonical backend suite from the repository root with `./scripts/test-backend.sh`; run frontend checks inside
   the web build or locally with the locked Node dependencies.

## Reproducible Milestone B fixture API smoke

Default Compose remains `BEFOREBUY_RESEARCH_MODE=OFFLINE`; research start returns `409 RESEARCH_OFFLINE` and performs
zero outbound requests. For a local, explicitly fixture-labelled smoke (never current market data):

```sh
BEFOREBUY_RESEARCH_MODE=FIXTURE docker compose up --build -d
docker compose exec api python backend/manage.py migrate --noinput
```

Bootstrap `GET /api/v1/session` and retain its cookie/CSRF token؛ `POST /api/v1/conversations`؛ `PATCH` the brief with
recipient/category/budget/use case؛ `POST .../brief/confirm`؛ then:

```http
POST /api/v1/conversations/{conversation_id}/research
Idempotency-Key: research-smoke-key-0001
X-CSRFToken: {token}
Content-Type: application/json

{"expected_brief_revision":1,"targets":[{"source_id":"synthetic-appliance-v1"},{"source_id":"synthetic-electronics-v1"}]}
```

Poll `GET /api/v1/research-jobs/{job_id}` or follow the returned operation `events_url`. Expected terminal fixture result:
`SUCCESS`, `fixture_labeled=true`, two snapshots with `canonical_url=null` and explicit `fixture_label`. GET/status/replay
does not start work. To cancel, `POST /api/v1/research-jobs/{job_id}/cancel` with CSRF. To restore the safe default:

```sh
docker compose up -d --force-recreate api
```

with `BEFOREBUY_RESEARCH_MODE` unset/`OFFLINE`. It must not silently emit fixture evidence.

## Explicit Phase 9.2 local real-offer pilot

Default Compose remains `OFFLINE`. After reading `source-feasibility.md` and without changing public deployment، apply
migrations and explicitly install the reviewed exact-product policies:

```sh
docker compose exec api python backend/manage.py migrate --noinput
docker compose exec api python backend/manage.py configure_market_sources --enable
BEFOREBUY_RESEARCH_MODE=LIVE docker compose up --build -d api web
```

Open `http://127.0.0.1:58080/copilot`، edit/confirm a brief، enter one to three exact HTTPS product URLs and select
«بررسی پیشنهادها». Only Torob `/p/`، the two reviewed Technolife product IDs، and exact `/product/` paths at Bkalaa/
Takkalaban are configured. Search/query/fragment URLs remain rejected. Network/policy/extraction failures are shown and
never fall back to fixture. To restore the safe default and disable policies:

```sh
docker compose exec api python backend/manage.py configure_market_sources --disable
docker compose up -d --force-recreate api
```

## Controlled LIVE pipeline verification

`LIVE` accepts only `{source_id, url}` targets where `url` is an exact product URL and its hostname matches an existing
`SourcePolicy`; a domain alone is rejected. `tests.integration.test_research_pipeline` starts a loopback HTTP server،
while a test-only connector maps an already public-validated synthetic address to that server. It otherwise uses the
production API، policy validation، fetcher، extractor، identity reconciliation، PostgreSQL publication and event ledger.
This verifies controlled-source plumbing، not permission or quality for a public source.

```sh
cd backend
uv run --project .. python manage.py test \
  tests.integration.test_research_pipeline \
  tests.integration.test_research_concurrency \
  tests.unit.test_safe_fetch --settings=config.settings.test --keepdb
```

No public deployment, provider call, broad crawl, product ranking, memory or credential storage belongs to Milestone B.
