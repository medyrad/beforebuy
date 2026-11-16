# Source-to-screen checkpoint — 2026-11-16

شاخه: `002-personalized-shopping-copilot`؛ baseline: `d989ea1a23c560a4144dd7a72ea5c6b978f21e28`.
گزارش قبلی بدون تغییر در `docs/archive/market-manual-checkpoint-handoff.md` محفوظ است.

## نتیجهٔ واقعی

**Source-to-screen blocked at TCP connection**

هدف بررسی‌شده: https://takkalaban.com/product/philips-na230/ ؛ شواهد استخراج JSON-LD قبلی تاریخی است، نه قیمت امروز.
دو درخواست مستقیم، متوالی، با همان URL/headerهای SafeFetcher و بدون proxy اجرا شد:

| محیط / شروع UTC | DNS | TCP | کل زمان |
|---|---|---|---|
| host / 11:29:57.967577 | 109.70.78.2، 4.3387s | TimeoutError، 10.0012s | 14.3486s |
| API-container / 11:30:52.775880 | 109.70.78.2، 0.2984s | TimeoutError، 10.0161s | 10.3207s |

هر دو: proxy environment موجود نبود؛ system proxy types خالی بود. هیچ مقدار proxy یا کلیدی چاپ نشد.
TLS، HTTP headers، body و extraction نرسیدند؛ publication اجرا نشد. این شاهد علت پایین‌دستی
مانند ISP/firewall/origin را تعیین نمی‌کند و خطای parser، HTTP rejection یا transport اختصاصی برنامه را ثابت نمی‌کند.
طبق شرط توقف، SafeFetcher و API زنده دوباره در این محیط امتحان نشدند؛ منبع جایگزین مستقلِ قابل‌دسترسی احراز نشد.
مصرف این checkpoint **۲ از۱۲ تلاش**، بدون redirect/fallback؛ **۱۰ واحد باقی**. دفتر قبلی۴ از۳۰ حفظ شده است.
پیشنهاد واقعی استخراج/ذخیره/نمایش‌داده‌شده: **صفر**. دادهٔ fixture یا دستی به‌عنوان موفقیت شمرده نشد.

## اصلاح مستقل و آزمون

ابزار موجود `scripts/diagnose-research.py` اکنون exact targetهای بررسی‌شده، حالت مستقیم بدون proxy،
زمان/مرحلهٔ DNS→TCP→TLS→headers→body→extraction و شمارش تلاش را گزارش می‌کند؛ body ذخیره/چاپ نمی‌شود.
safe mode همان SafeFetcher واقعی را با مشاهده‌گر زمان‌بندی به‌کار می‌گیرد؛ TLS/SSRF/IP pinning و سقف‌ها تضعیف نشده‌اند.
regression گزارش مرحلهٔ شکستِ قدیمی پس از fallback ابتدا قرمز و سپس اصلاح شد.
هیچ تغییر در transport تولیدی، extractor، UI، ویژگی دستی، provider یا schema پایگاه داده انجام نشد.

فرمان‌های اجراشده از ریشه:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests/unit -p test_research_diagnostic.py -v
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests/unit -p test_safe_fetch.py -v
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests/unit -p test_extractors.py -v
```

به‌ترتیب۸،۲۱ و۸ تست کشف/اجرا/موفق؛ مجموع۳۷، صفر skipped/failure/error. شبکهٔ این تست‌ها stub یا loopback است، نه دریافت بازار.
پوشش شامل header یکسان، TCP/TLS/HTTP مجزا، محدودیت fallback، رد IP خصوصی، عدم افشای proxy، استخراج مصنوعی و عدم publication است.
build یا مرورگر تکرار نشد: UI تغییری نکرد و استخراج زنده پیش‌نیاز مسیر واقعی بود.
Spec Kit analyze محدود FR-096→T105/T106: یک الزام، دو task، پوشش۱۰۰٪، تعارض بحرانی/ابهام/تکرار صفر؛
implement فقط اصلاح تشخیص T105. T106 و T066، T101 و feature001 T039 باز هستند؛ همگرایی کامل ادعا نمی‌شود.

## تنها اقدام بعدی موردنیاز

روی یک شبکه/میزبان مستقلِ ازقبل‌موجود، از ریشهٔ همین checkout فرمان زیر را اجرا و JSON و exit status را ارسال کنید:

```sh
python3 scripts/diagnose-research.py --target takkalaban-na230 --layer direct --max-attempts 1
```

فقط Python3 و کد مخزن لازم است؛ بدون نصب Django، API key، database، backup، credential export یا public deployment.
اگر شکست خورد توقف کنید. فقط پس از استخراج موفق، همان فرمان با `--layer safe` قابل مقایسه است؛
هر اجرا از۱۰ واحد باقی کم می‌کند. آماده‌بودن دستور، موفقیت checkpoint نیست.
پس از موفقیت باید API عادی، هویت/واحد/موجودی/زمان/هزینهٔ نامعلوم، مالکیت و mobile/desktop reload واقعاً بررسی شود.

## حفاظت اجرا و داده

فرمان canonical بدون تغییر:

```sh
COPILOT_MASTER_KEYRING_PATH=/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key bash scripts/dev-with-credentials.sh up -d
```

هیچ restart/build، تغییر تنظیمات AI mock یا research OFFLINE، فعال‌سازی policy، خواندن کلید، فراخوانی مدل،
خرید سرویس، تغییر DNS/VPN/proxy یا deployment عمومی انجام نشد. volumeها، backupها، secretها و تصاویر نامرتبط حفظ شدند.
بررسی فقط سه setting غیرمحرمانه در API جاری تأیید کرد: `COPILOT_AI_MODE=mock`، `BEFOREBUY_AI_MODE=mock` و `BEFOREBUY_RESEARCH_MODE=OFFLINE`.
تغییرات مرتبط فقط commit/push می‌شوند؛ hash محلی و remote مشاهده‌شده در پاسخ نهایی ثبت می‌شود، نه ادعای پیشاپیش همگامی.
