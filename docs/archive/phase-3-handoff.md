# تحویل Phase 3 — M1 backend

**تاریخ اجرا:** ۱۴ نوامبر ۲۰۲۶  
**وضعیت:** M1 backend implemented and verified؛ محصول کامل آماده نیست.

## workflowهای Spec Kit که واقعاً اجرا شدند

1. `$speckit-tasks`: `setup-tasks.sh --json` اجرا شد و `tasks.md` canonical با ۴۳ task ساخته شد: ۳۲ مورد M1،
   ۵ مورد M2، ۳ مورد M3 و ۳ مورد M4. فرمت checkboxها validate شد و مورد نامعتبر صفر بود.
2. `$speckit-analyze`: prerequisite check با `--require-spec --require-tasks --include-tasks` اجرا شد. critical یا
   requirement بدون پوشش پیدا نشد. سه مورد HIGH—نسخه‌های پیشنهادی قدیمی، عبارت قدیمی «tasks ساخته نشده»، و drift
   mode mock—در artifactها اصلاح شدند. مورد low-impact حل‌نشده‌ای که مانع M1 باشد باقی نماند.
3. `$speckit-implement`: prerequisite check اجرا شد؛ checklistهای `requirements.md` برابر ۳۰/۳۰ و
   `technical-plan.md` برابر ۲۵/۲۵ پاس بودند. اجرا عمداً فقط taskهای M1 بود؛ M2–M4 دست‌نخورده‌اند.

این نتایج به‌تنهایی application-test success نبودند؛ verification مستقل پایین اجرا شد.

## سه correction فنی Phase 3

- **CSRF مهمان ناشناس:** `CsrfViewMiddleware` فعال است؛ همهٔ viewهای unsafe از base صریح `csrf_protect` عبور
  می‌کنند و bootstrap با `ensure_csrf_cookie` cookie استاندارد Django می‌دهد. به رفتار anonymous
  `SessionAuthentication` اتکا نشده است. missing/invalid token و Origin/Host نامعتبر تست شده‌اند.
- **access در برابر retention:** هر Analysis expiry ثابت `created_at + 90d` دارد. GuestContext و Django session
  فقط پس از persist موفق analysis جدید تا expiry همان analysis تمدید می‌شوند؛ read/edit/retry/feedback لغزان نیستند.
  سناریوی day-89 → day-179 تست شد. cookie loss یعنی عدم recovery و cross-device access.
- **raceهای clear/create و retry:** initial create epoch مهمان را snapshot می‌کند؛ clear زیر lock همان GuestContext
  epoch را افزایش و rows را حذف می‌کند؛ publication زیر همان lock epoch را دوباره می‌سنجد. edit/retry token تازه
  می‌گیرند و تنها token جاری می‌تواند report منتشر کند. generator بیرون transaction/lock اجرا می‌شود. delete هنگام
  retry، clear هنگام create و دو retry رقیب با barrierهای deterministic روی PostgreSQL تست شدند.

## اجزای پیاده‌سازی‌شده

- Django settings جدا، DRF routes و database session ownership در `backend/`.
- مدل‌ها و migration اولیه برای GuestContext، Analysis، CurrentReport و UsefulnessFeedback.
- normalization تومان، engine خالص `PDA-CAT-v0.3`، dimensionها، precedence، evidence با attribution و unknown/action.
- `ExplanationGenerator` کوچک، mock صریح `MOCK_ASSISTED`، allowlist claim/content validation و fallback
  `RULE_BASED_LIMITED`. هیچ live provider فراخوانی نشده است.
- API bootstrap، create/list/read/edit/delete، clear، reanalysis و feedback put/delete با 400/403/404/409 envelope.
- command پاک‌سازی analysis/context/session و Compose توسعهٔ api+db.
- OpenAPI 3.1، مثال اجرایی، route parity test و راهنمای smoke cookie/CSRF.

## dependencyهای exact

| Component | Resolved version |
|---|---:|
| Python local / image | `3.12.4` / `3.12.12-slim` |
| uv | `0.13.0` |
| Django | `5.2.16` |
| Django REST Framework | `3.17.1` |
| psycopg / psycopg-binary | `3.3.6` / `3.3.6` |
| gunicorn | `23.0.0` |
| PyYAML (dev) | `6.0.3` |
| PostgreSQL image | `18.1-alpine` |

نسخه‌ها در `uv.lock` pin شده‌اند. plan اولیه Django `5.2.17` و DRF `3.18.1` را proposal می‌دانست؛ metadata
واقعی سازگار هنگام اجرا به نسخه‌های بالا resolve شد. `docker compose build api` نصب lock را موفق انجام داد. نصب
محلی تازهٔ `uv sync --frozen` در این ماشین برای wheel macOS `psycopg-binary` پس از ۳ retry/۱۰۰.۷ ثانیه timeout
شد؛ محیط محلی cache-backed موجود و image مستقل هر دو import/test موفق دارند. این محدودیت شبکه است، نه lock drift.

## verification تازه

| Check | Result |
|---|---|
| backend skill validator | `Skill is valid!` |
| `docker compose build api` | موفق؛ ۹ runtime package از lock نصب شد |
| Compose DB/API startup | هر دو بالا؛ API روی `58000` و DB روی `55439` |
| bootstrap smoke | `GET /api/v1/session` → `200` |
| cookie/CSRF create smoke | `POST /api/v1/analyses` → `201`, `MOCK_ASSISTED`, rubric `PDA-CAT-v0.3` |
| Django check | بدون issue |
| migration drift | `No changes detected` |
| empty PostgreSQL migration | همه migrationها، شامل `analysis.0001_initial` و `sessions.0001_initial`, موفق |
| full PostgreSQL suite نهایی | `60 tests`, همگی پاس در `3.905s` |
| focused schema/evidence/OpenAPI cycles | red evidence ثبت شد؛ سپس در suite نهایی سبز |

پس از verification، database موقت `beforebuy_m1_empty` حذف و containerهای development با exit code صفر متوقف
شدند؛ volume اصلی development حفظ شده و با `docker compose up -d --wait` دوباره قابل استفاده است.

## startup و smoke محلی

```bash
cp .env.example .env
docker compose build api
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up -d --wait
curl --fail --cookie-jar /tmp/beforebuy-cookies.txt http://127.0.0.1:58000/api/v1/session
```

sequence کامل POST همراه extraction استاندارد CSRF در `quickstart.md` و `docs/backend-operations.md` است.

## taskها و مرز توقف

M1 یعنی `T001–T025`, `T028–T029`, `T031–T032`, `T035–T037`. تنها همین شناسه‌ها complete می‌شوند.
`T026–T027`, `T030`, `T033–T034` (M2)، `T038–T040` (M3) و `T041–T043` (M4) unchecked هستند.

## محدودیت‌ها و ادامه

- AI فقط mock است؛ rating آن live-AI metric نیست. provider/model، timeout/retry/cost ceiling و live evaluation در M3.
- React/RTL UI و browser journey وجود ندارند؛ skillهای frontend/browser نصب نشده‌اند.
- Compose فقط development است؛ production gateway، TLS، backup/restore، rollback و deploy verification در M4.
- code-intelligence tool نصب نشد. اکنون vertical slice وجود دارد، اما benchmark trigger یک کار آینده و جداست.
- هیچ latency، completion time، AI quality/cost یا production capacity اندازه‌گیری نشده است.

## artifactهای اصلی

- `specs/001-purchase-decision-analysis/tasks.md`
- `backend/analysis/`, `backend/tests/`, `backend/config/`
- `pyproject.toml`, `uv.lock`, `compose.yaml`, `deploy/api.Dockerfile`
- `docs/backend-operations.md`, `specs/001-purchase-decision-analysis/quickstart.md`
- handoff پیشین: `docs/archive/phase-2-handoff.md`

M1 backend implemented and verified
