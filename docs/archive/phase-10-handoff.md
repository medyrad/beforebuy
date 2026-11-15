# تحویل Phase 10 — Milestone C / Choice Desk

تاریخ: 2026-11-15؛ baseline: `ccb90adf5d5270175111e963d39a46fe12da352b`؛ branch: `002-personalized-shopping-copilot`.

**Milestone C Choice Desk implemented and verified with labelled fixtures — live market coverage and live AI remain pending.**
پوشش بازار زنده و AI زنده همچنان pending؛ Milestone D اجرا نشده است.

## دامنه و workflow

- Spec Kit تنها workflow owner است؛ prerequisites، analyze و implement برای T024–T031 اجرا شدند. checklist
  requirements برابر 16/16 بود و تغییر نکرد؛ extensions.yml/hook ثبت‌شده وجود ندارد.
  T024–T031 تکمیل و علامت‌گذاری شدند؛ شماره یا وضعیت taskهای تاریخی نامرتبط تغییر نکرد.
- تحلیل محدود ۱۰ نیاز مرتبط (FR-012/013/015/016/017/018/019/031/063/064) را به ۸ task نگاشت؛ coverage در این scope
  100%، task بدون نگاشت صفر، critical صفر. ناسازگاری سقف قدیمی ۲۰ گزینه، وضعیت planned قرارداد ChoiceSet و
  attributionهای fixture در اسناد اصلاح شد. این تحلیل ادعای convergence کل feature نیست.
- مهارت‌های project، Django/DRF، frontend-design، TDD، debugging، verification و playwright-cli از catalog موجود
  و فایل‌های نصب‌شده استفاده شدند؛ هیچ ابزار، framework، dependency یا subagent تازه‌ای اضافه نشد.
- evidence models و controlled fixtures اجازهٔ توسعهٔ offline Milestone C می‌دهند؛ موفقیت public extraction فقط
  gate پوشش live است. T066 و T013/T018/T019 باز مانده‌اند؛ T039 هر دو feature و milestoneهای بعدی کامل نشده‌اند.

## پیاده‌سازی و قواعد

- migration افزایشی `0010_shoppingbrief_comparison_choiceset`، پروفایل صریح comparison و ChoiceSet immutable با
  revision/epoch/rule version/snapshot/freshness اضافه شد. آیتم‌ها JSON داخلی‌اند؛ جدول تکراری ChoiceItem ساخته نشد.
  داده/volume توسعه حذف یا reset نشد. retention/delete از conversation ارث می‌رسد؛ read/compare/demo تمدید نمی‌کنند.
- COPILOT-RANK-v0.1 بدون وزن یا امتیاز ۰–۱۰۰: شرط قطعی و ترجیح؛ satisfied/failed/unknown جدا؛ STRICT پیش‌فرض،
  FLEXIBLE فقط با تأیید؛ ارسال و هزینهٔ اجباری نامعلوم هرگز صفر نیستند. known total از قیمت کالا جداست.
- دسته‌ها: سازگار، حل‌نشده، ناسازگار. coverage سپس ترجیح‌های مستند، و فقط در صورت ترجیح صریح هزینهٔ نهایی کمتر.
  UUID صرفاً ترتیب نمایش tie را پایدار می‌کند. شواهد stale/conflicting/unsupported و variant mismatch امتیاز مثبت ندارند.
  تناقض brief و شرط متنی حل‌نشده winner قطعی نمی‌سازند. هدیه از معیار گیرنده استفاده می‌کند؛ لذت هدف معتبری است.
- یک محصول موردنظر + حداکثر سه محصول جایگزین؛ merchant offerها جدا و متعلق به همان variant هستند.
  پیشنهاد کاملِ گران، پیشنهاد ارزان‌تر با ارسال نامعلوم را «قطعاً بالای بودجه» نمی‌کند؛ این حالت حل‌نشده می‌ماند.
  گزینهٔ ناموجود جایگزین نمی‌شود؛ نبود جایگزین پشتیبانی‌شده صریح است. unknownها، tradeoff، coverage و شرایط تغییر
  نتیجه قابل مشاهده‌اند. متن توضیح deterministic template است، نه پاسخ LLM.
- API جدید `/conversations/{id}/choices`، `/choices/candidates` و `/choices/demo` با مالکیت/CSRF/expiry و validation.
  publication زیر lock تغییر revision/epoch را دوباره بررسی می‌کند؛ نتیجهٔ دیررس رد می‌شود.
- سه نمونهٔ صریح در Product/Variant/Offer/Claim عادی ذخیره می‌شوند و همان engine/API/UI آینده را مصرف می‌کنند؛
  SYNTHETIC/CAPTURED_FIXTURE هرگز VERIFIED_SOURCE یا قیمت بازار فعلی نامیده نمی‌شوند.
- Concept 2 حفظ شد: conversation rail، brief ribbon، جدول دسکتاپ/کارت‌های responsive، disclosure و کشوی منابع،
  RTL/Vazirmatn، focus/keyboard و ناوبری موبایل با state حفظ‌شده. تغییر brief نتیجهٔ قبلی را فوراً پنهان/نامعتبر می‌کند.
  rail در راست و میز در چپ است؛ پنل پژوهش پیش‌فرض بسته است و با بازشدن، درخواست شبکه اجرا نمی‌کند.
  routing پیش‌فرض legacy، streaming و cancellation حفظ شدند؛ memory/API-key settings وجود ندارند.

## سه مقایسهٔ قابل تکرار

همهٔ محصولات و قیمت‌های این جدول مصنوعی‌اند، نه دادهٔ بازار:

| نیاز تأییدشده | نتیجه |
|---|---|
| electronics، SELF، ENJOYMENT، سقف۱۰ میلیون، portable=true قطعی | آ۸ میلیون و پ۹ میلیون tie؛ ب۷ میلیون portable=false و ارسال نامعلوم ناسازگار. سقف۸ میلیون فقط آ را سازگار می‌گذارد. |
| home، HOUSEHOLD، سقف۶ میلیون، dishwasher_safe=true قطعی | آ۶ میلیون سازگار؛ ب۴ میلیون شرط شست‌وشو را نقض می‌کند؛ پ۷ میلیون بالای سقف و شست‌وشو/ارسال نامعلوم. |
| sports، GIFT، سقف۲ میلیون، size_eu=42 برای RECIPIENT | آ۲ میلیون سازگار؛ ب سایز۴۰ ناسازگار؛ پ سایز۴۲ و قیمت۱٫۸ میلیون با ارسال نامعلوم حل‌نشده. |

PRACTICAL نیز با همان قواعد بودجه/شرط بررسی می‌شود، بدون تشخیص impulsivity یا hardship.

## verification

- REDهای اولیه: نبود engine/API/UI؛ سپس unknown offer attribution و تناقض brief. اصلاح و GREEN مشاهده شد.
- canonical PostgreSQL: `./scripts/test-backend.sh --keepdb --verbosity 1` → **260 discovered/run، 260 passed**،
  صفر skipped/failed/errors در 58.735s. تست migration تاریخی schema را روی 0007 باقی می‌گذاشت؛ cleanup به graph
  leaf اضافه شد. اجرای نخست 258 passed/1 error بود و موفق گزارش نمی‌شود.
- focused ranking/API/invariants بعد از اصلاح JSON null و provenance: 17/17؛ race با دو connection PostgreSQL
  و Event/row lock رد انتشار دیررس را بررسی کرد. hand-authored موارد بودجه، enjoyment، هدیه، variant mismatch،
  stale/conflict، missing shipping، tie و sparse evidence همراه invariantهای ترتیب/prose اجرا شدند.
- migrationها روی دیتابیس تستِ تازه `test_beforebuy_phase10_migrations_20261115` اعمال شدند؛ نبود آن پیش از اجرا
  بررسی شد، سپس 6/6 تست API/هم‌زمانی با DiscoverRunner و keepdb موفق بود. این دیتابیس مصنوعی جدا حفظ شده است.
  مورد چندفروشنده‌ای ابتدا RED و بعد همراه 12/12 تست pure و مجموعهٔ نهایی 260تایی GREEN شد.
- frontend: آخرین مجموعهٔ بررسی‌شده 19/19؛ خطای قبلی تایپ پیش از enabled شدن ورودی در تست‌های stream با
  انتظار صریح و act اصلاح شد. typecheck، lint و build موفق؛ build واقعی Compose/NGINX نیز انجام شد.
- مرورگر واقعی پشت NGINX: `copilot-choice-desk.spec.ts` → **2/2 passed** در 390/1440، keyboard/focus و
  Escape، 200% zoom بدون overflow ضروری، منابع، brief-edit/recompute، حفظ draft و لغو واقعی سرور با status=CANCELLED.
  axe در هر دو عرض و zoom برابر صفر serious/critical؛ route legacy نیز موفق بود. هیچ API/SSE/cancel این دو تست mock نشده است.
  REDهای مرورگر: selector/انتظار bootstrap، JSON-null خالی، focus dialog، min-width legacy در zoom و race پنجرهٔ کوتاه stream.
  اصلاح‌ها: پاسخ null معتبر، trap Tab/Shift-Tab، width/RTL محدود به Copilot، reduced-motion و کلیک stop در اولین DOM update.
  screenshotهای `artifacts/screenshots/copilot-phase10-1440.png` و `copilot-phase10-390.png` باز و بازبینی شدند.
- رگرسیون browserِ گفت‌وگو/brief و پنل captured offer در `copilot-milestone-a.spec.ts`: **2/2 passed**؛
  screenshotهای این رگرسیون فقط در `.runtime/phase10-legacy-browser-results` نوشته شدند و چهار تصویر قبلی دست‌نخورده‌اند.
- Django check و migration drift موفق؛ runtime مؤثر: `research_mode=OFFLINE`، `ai_mode=mock`،
  `enabled_policies=0`. هیچ درخواست public-source یا LLM، تغییر سقف هزینه، deployment عمومی یا volume reset انجام نشد.

## راه‌اندازی و نمایش محلی

با .env موجود و AI mock، از root:

```sh
docker compose up -d db
docker compose run --rm --no-deps api python backend/manage.py migrate --noinput
BEFOREBUY_RESEARCH_MODE=OFFLINE docker compose up -d --build api web
```

بازکردن `http://127.0.0.1:58080/copilot` → گفت‌وگوی تازه → در موبایل میز انتخاب → ویرایش brief.
category دقیق electronics/home/sports، مخاطب، بودجه و معیار اختیاری را ذخیره و تأیید کنید؛ در انتخاب محصولات،
همان دستهٔ آموزشی را بارگذاری و «ساخت مقایسه» را بزنید. هر دسته را در گفت‌وگوی تازه امتحان کنید.
منابع عمومی را فعال نکنید؛ token لازم نیست. جزئیات و تست‌ها در quickstart feature ثبت شده‌اند.

## gateها و Git

T066/public-source repeatable extraction، T013/T018/T019، T039 و live AI/region/cost/human review بازند.
هیچ ادعای آمادگی انتشار عمومی یا convergence کل محصول وجود ندارد. توقف پیش از Milestone D.

handoff قبلی بدون تغییر در `docs/archive/phase-9.3-handoff.md` آرشیو شد.
مسیر Git: همین branch روی `origin` پروژهٔ `medyrad/beforebuy`، بدون merge یا force-push.
حذف نامرتبط `test.txt` و چهار screenshot قدیمی خارج stage باقی می‌مانند؛ hash و نتیجهٔ push در گزارش نهایی ارائه می‌شود.
اسرار، .env، database، runtime trace و دادهٔ حساس وارد Git نمی‌شوند.
