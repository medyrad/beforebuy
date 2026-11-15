# Beforebuy — همراه خرید

دستیار گفت‌وگویی فارسی برای روشن‌کردن نیاز خرید و مقایسهٔ مبتنی بر شواهد است؛ ادعای پیش‌بینی علمی پشیمانی یا پوشش همهٔ بازار ندارد.

## وضعیت فعلی

بازطراحی محدود UX روی feature `002-personalized-shopping-copilot` جریان اصلی را گفت‌وگویی می‌کند. مسیر `/` و
`/copilot` دستیار جدید و `/legacy` تجربهٔ قبلی هستند؛ لینک‌های قبلی `/?analysis=...` حفظ شده‌اند.
AI پیش‌فرض mock و research OFFLINE است؛ داشتن کلید به معنی فعال‌شدن، اعتبارسنجی یا مجوز هزینه نیست.
نتایج دقیق آزمون و وضعیت بازبینی بصری در [تحویل فعلی](docs/handoff.md) ثبت می‌شوند. live evaluation و انتشار عمومی بازند.

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
- [Specification دستیار خرید جاری](specs/002-personalized-shopping-copilot/spec.md)
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
مسیر Compose/NGINX برای verification واقعی `http://127.0.0.1:58080/` است. composer پیام اول را خودکار به گفت‌وگو
تبدیل می‌کند؛ تاریخچه، تنظیمات و شناخت من در ناوبری بالا هستند. فقط با شواهد کافی مقایسه/قیمت نمایش داده می‌شود.
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
