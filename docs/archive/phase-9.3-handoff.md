# تحویل Phase 9.3 — تشخیص اتصال و اصلاحات محدود

تاریخ: 2026-11-15؛ baseline: `40a1add3d5459291a2bda9f78eda8e367dacd8c5`؛ branch: `002-personalized-shopping-copilot`.

**Real-source offer pilot partially complete — source blockers documented**

## نتیجه و علت‌یابی

این فاز کاملاً local و بدون توکن/فراخوانی AI اجرا شد. Docker Desktop خاموش بود؛ برنامهٔ موجود راه‌اندازی و همان
volume توسعه استفاده شد. هیچ volume reset، زیرساخت جدید، deployment عمومی یا subagent وجود نداشت.

هدف دقیق: `https://torob.com/p/bb037069-fba8-4964-a758-6adcec22898f/q60d/`.
در 08:03:36–08:09:30 UTC، DNS فقط `81.12.31.29` از نوع IPv4 برگرداند:

| مسیر | نتیجه |
|---|---|
| میزبان مستقیم | DNS و TCP موفق؛ TLS/SNI معتبر؛ HTTP 490 |
| API container مستقیم | همان IPv4؛ TCP و TLS موفق؛ HTTP 490 |
| SafeFetcher میزبان/container | HTTP 490 → HTTP_STATUS؛ پیش از body/extraction متوقف شد |
| API واقعی از NGINX | یک request؛ NO_SUPPORTED_SOURCES؛ snapshot شکست PostgreSQL؛ صفر offer |

job تشخیصی: `deccf843-4d5f-401c-80d5-35e50ccb60de` در 08:07:33 UTC، snapshot برابر `FAILED/HTTP_STATUS`.
این درخواست مقایسهٔ اولیه API بود؛ بعد از preflight ناموفق هیچ retry پایلوت API اجرا نشد. فرمان pilot در 08:09:30
نیز preflight را اجرا کرد، 490 گرفت و صریحاً صفر API job ساخت. UI تغییر نکرد و browser suite دوباره اجرا نشد.

مرز شکست اثبات‌شده HTTP پس از TLS معتبر است. علت صدور 490 توسط endpoint (edge/origin/access policy یا علت دیگر)
هنوز معلوم نیست. این مشاهده ناشی از نبود توکن AI یا انتخاب اولین IP نیست؛ تنها یک IP وجود داشت. timeout تاریخی
و captured/tool content با شبکهٔ فعلی هم‌ارز نیستند. موفقیت روی سرور/شبکهٔ دیگر فرض نشده است. proxy محیطی یا
system proxy در میزبان/container مشاهده نشد؛ هیچ مسیر proxy یا bypass افزوده نشد.

## اصلاحات و workflow

- Spec Kit prerequisites، analyze و implement فقط برای `T067–T070` اجرا شدند؛ checklist برابر 16/16، extension hook
  ثبت‌شده وجود نداشت. FR-061/062 به چهار task جدید map شدند؛ نیازمندی بدون task یا تعارض constitution در scope صفر.
  ناسازگاری historical/current source status اصلاح شد. شمارهٔ taskهای قدیمی تغییر نکرد.
- مهارت‌های project، bounded research، debugging، Django/DRF، TDD و verification استفاده شدند.
- SafeFetcher حداکثر دو IP متمایز از یک پاسخ DNS کاملاً public-validated را قبل از ارسال HTTP امتحان می‌کند.
  deadline request/job مشترک، سهم زمانی connection محدود، Host/SNI/certificate اصلی و socket/capacity cleanup حفظ شدند.
  اتصال numeric socket نیازمند lookup دوباره نیست. fallback در request/domain budget موجود حساب می‌شود؛ HTTP، parser
  یا policy failure retry ندارد و mixed public/private همچنان رد می‌شود.
- configure_market_sources تاریخ review، readiness، متن شواهد و URL اسناد موجود را در toggle حفظ می‌کند. row تازه exact timestamp=null
  و اشاره به evidence تاریخ 2026-11-15 دارد؛ تاریخ دقیق جعل نمی‌شود. timestampهای قدیمیِ تولیدشده هنگام toggle
  برای audit حفظ شدند ولی review تازه محسوب نمی‌شوند. enable شدن row اثبات technical readiness نیست.
- دو فرمان diagnostic/pilot قابل‌تکرار اضافه شدند؛ pilot فقط پس از extraction موفق preflight دو conversation تازه
  ایجاد می‌کند تا repeat از cache نباشد. مسیر موفق آن هنوز اجرا نشده است.

## verification و مصرف

- RED: سه تست fallback قبل اصلاح و دو تست provenance قبل اصلاح شکست مورد انتظار داشتند.
- focused transport/provenance: 21/21؛ سپس دو تست TLS cleanup و budget اضافه شدند.
- canonical PostgreSQL: `./scripts/test-backend.sh --keepdb --verbosity 1` → **242 discovered/run، 242 passed،
  صفر skipped/failed/errors** در اجرای نهایی 78.066s. پاسخ‌های 4xx و DisallowedHost در تست‌های negative مورد انتظار بودند.
- regression تکمیلی حفظ متن شواهد ابتدا RED و سپس 2/2 provenance GREEN شد؛ Django check، migration drift،
  OpenAPI YAML، compile اسکریپت‌ها و diff whitespace موفق بودند.
- AI/provider calls صفر. 10 تلاش outbound با خروجی بررسی‌شده ثبت شد؛ خروجی نهایی فرآیند تشخیصی اولیهٔ دو‌تلاشی
  نگه‌داری نشد، پس دو تلاش کامل محافظه‌کارانه رزرو شد: **12/30 سقف مصرف/رزرو**، بدون reset بودجه.
- host/container direct، SafeFetcher، API و فرمان pilot failed-preflight واقعاً اجرا شدند؛ body/secret چاپ یا commit نشد.
- runtime مؤثر پس از reset: `research_mode=OFFLINE`، `ai_mode=mock`، `enabled_policies=0`؛ db/api/web healthy.

## فرمان‌های ادامهٔ کار

از ریشه، فقط در allowance باقی‌مانده:

```sh
docker compose exec -T api python scripts/diagnose-research.py --layer safe
```

پس از رفع HTTP failure و با رزرو حداکثر 16 تلاش برای یک اجرای pilot:

```sh
docker compose exec -T api python backend/manage.py configure_market_sources --enable
BEFOREBUY_RESEARCH_MODE=LIVE docker compose up -d --no-build --force-recreate api
docker compose exec -T api python scripts/pilot-reviewed-offer.py
```

بعد از هر نتیجه، بازگشت صریح و بررسی واقعی:

```sh
docker compose exec -T api python backend/manage.py configure_market_sources --disable
BEFOREBUY_RESEARCH_MODE=OFFLINE docker compose up -d --no-build --force-recreate api
docker compose exec -T api python backend/manage.py shell -c 'from django.conf import settings; from analysis.models import SourcePolicy; print(settings.BEFOREBUY_RESEARCH_MODE, SourcePolicy.objects.filter(live_enabled=True).count())'
```

انتظار `OFFLINE 0` است. فرمان موفق pilot، browser success و اجرای شبکهٔ دیگری ادعا نشده‌اند.

## gateها و Git

T066 باز است: صفر offer زنده، سه فروشندهٔ comparable در API/UI محقق نشده و fresh successful repeat نداریم.
T013/T018/T019 و T039 هر دو feature همچنان باز؛ این فاز crawler/live AI/public release را آماده اعلام نمی‌کند.
T067–T070 اصلاحات و تشخیص را پوشش می‌دهند و پذیرش مشروط T066 را جایگزین نمی‌کنند.

handoff قبلی در `docs/archive/phase-9.2-handoff.md` آرشیو شد. فقط code/test/spec/docs/scripts مرتبط stage می‌شوند؛
حذف نامرتبط test.txt و چهار screenshot قبلی خارج commit باقی می‌مانند. push به branch/remote موجود بدون force است.
