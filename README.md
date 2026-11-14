# Purchase Regret Predictor

دستیار مستقل تصمیم‌گیری برای خرید است که به کاربر کمک می‌کند بسنجد آیا خرید یک تلفن همراه با نیازها، بودجه و شرایط فعلی او سازگار است یا نه. این محصول قرار نیست پشیمانی آینده را با دقت اعتبارسنجی‌شده پیش‌بینی کند؛ خروجی آن باید تصمیم‌یار، توضیح‌پذیر و متکی به اطلاعات ارائه‌شده باشد.

## وضعیت فعلی

**Phase 6.2 — development environment corrections** محلی پیاده و verify شده است. Django/DRF API، engine قطعی،
persistence، رابط React فارسی/RTL، history، browser journey، adapter محدود AvalAI و بستهٔ production سه‌سرویسی موجودند.
mode پیش‌فرض همچنان mock است؛ live evaluation، target-host release gates و deployment عمومی pending هستند.

## راهنمای اسناد

- [خلاصه محصول](docs/product-brief.md)
- [تصمیم‌ها، پیش‌فرض‌ها و پرسش‌های باز](docs/decisions.md)
- [فهرست ابزارها و مهارت‌ها](docs/tooling.md)
- [تحویل فعلی](docs/handoff.md)
- [آرشیو تحویل Phase 0](docs/archive/phase-0-handoff.md)
- [آرشیو تحویل Phase 1](docs/archive/phase-1-handoff.md)
- [آرشیو تحویل Phase 1.1](docs/archive/phase-1.1-handoff.md)
- [آرشیو تحویل Phase 2](docs/archive/phase-2-handoff.md)
- [آرشیو تحویل Phase 3](docs/archive/phase-3-handoff.md)
- [آرشیو تحویل Phase 6](docs/archive/phase-6-handoff.md)
- [عملیات backend](docs/backend-operations.md)
- [قانون اساسی Spec Kit](.specify/memory/constitution.md)
- [Specification تحلیل تصمیم خرید](specs/001-purchase-decision-analysis/spec.md)
- [برنامه فنی Phase 2](specs/001-purchase-decision-analysis/plan.md)

## راه‌اندازی توسعه

```bash
cp .env.example .env
docker compose build api
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up -d --wait
curl --fail http://127.0.0.1:58000/api/v1/session

# از ریشهٔ repository؛ فقط backend/tests را اجرا می‌کند
scripts/test-backend.sh

cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

رابط در `http://127.0.0.1:5173/` باز می‌شود و `/api` را از proxy هم‌origin به backend می‌فرستد.
پورت‌های قابل‌تنظیم API و PostgreSQL توسعه فقط روی `127.0.0.1` منتشر می‌شوند.

smoke کامل cookie/CSRF و فرمان‌های تست/frontend در
[`quickstart.md`](specs/001-purchase-decision-analysis/quickstart.md) ثبت شده‌اند. output عادی فعلی mock با
`mode=MOCK_ASSISTED` است و نباید live AI تلقی شود.

برای live mode فقط در region پشتیبانی‌شده، متغیرهای backend را در فایل محلی `.env` تنظیم کنید؛ key را در chat،
repository یا متغیرهای Vite قرار ندهید. راهنمای gate و command ارزیابی در quickstart آمده است.

## Spec Kit و ادامه کار

Spec Kit به‌صورت project-scoped و با نسخه pin‌شده نصب می‌شود. مسیر `.tools/` در Git ثبت نمی‌شود. برای بازسازی ابزار محلی:

```bash
mkdir -p .tools/bin .tools/uv-tools
UV_TOOL_DIR="$PWD/.tools/uv-tools" \
UV_TOOL_BIN_DIR="$PWD/.tools/bin" \
uv tool install specify-cli \
  --from git+https://github.com/github/spec-kit.git@v1.4.0
.tools/bin/specify --version
```

مهارت‌های Spec Kit با نام‌های `$speckit-*` در Codex فراخوانی می‌شوند. در شروع فاز بعد، ابتدا `AGENTS.md`، اسناد بالا و specification مربوط به همان feature را بخوانید. هیچ workflow برنامه‌ریزی موازی با Spec Kit ایجاد نکنید.
