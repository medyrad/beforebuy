# بررسی محدود OpenRouter و اصلاح فونت منوها — 2026-11-16

Baseline: `8cb7c12c7a542c5c5fb894cc49d0388cca79915b`؛ شاخه `002-personalized-shopping-copilot`.
نتیجهٔ این تحویل: اصلاح typography مستقل انجام شد؛ **اتصال رایگان OpenRouter پیاده/فعال نشده است**.
طبق شرط درخواست، integration مسدود دیگری ساخته نشد. T096 و feature001 T039 باز هستند.

## نتیجهٔ امکان‌سنجی

- فقط `nvidia/nemotron-3.5-lightning:free` با `nvidia/nvfp4` و
  `baidu/ernie-5.5-flash-preview:free` با `baidu` بررسی شدند. API عمومی هر دو قیمت ورودی/خروجی صفر نشان داد؛
  این مشاهده نه تأیید حساب است و نه صورتحساب. مدل انتخاب‌شده برای runtime: **هیچ‌کدام**.
- NVIDIA قرارداد trial، ثبت داده و الزامات export/sanctions دارد؛ پارامتر structured-output در endpoint بررسی‌شده
  فهرست نشده بود. Baidu structured-output را فهرست کرده، اما قرارداد regional access را مشروط و نگهداری/استفاده
  از محتوا را مجاز می‌کند. انطباق مسیر دقیق با کاربران/backend ایران و رضایت آگاهانهٔ داده هنوز احراز نشده است.
  «احراز نشدن» به معنی «ممنوعیت قطعی ایران» نیست. کیفیت فارسی هیچ‌کدام اندازه‌گیری نشد.
- منابع رسمی، قراردادهای upstream، quota تاریخ‌دار، شرایط حساب بدون شارژ و متن دقیق سؤال پشتیبانی در
  [free-provider-readiness.md](../specs/002-personalized-shopping-copilot/free-provider-readiness.md) ثبت شده است.
  هیچ پیام پشتیبانی از طرف کاربر ارسال نشده است.
- OpenRouter هنوز informational است. کلید آن را در فرم OpenAI/GapGPT وارد نکنید؛ فرم اختصاصی تا بسته‌شدن gate و
  اجرای T096 وجود ندارد. سپس pilot باید با اقدام محلی صریح «آزمایش رایگان»، حداکثر ۱۰ تلاش کل شامل retry/validation،
  سقف پولی صفر و بدون fallback/ابزار پولی پیاده شود. این کنترل‌ها requirement هستند، نه قابلیت تحویل‌شده.
- تماس generation واقعی: **۰**؛ usage/صورتحساب/ارزیابی مکالمهٔ واقعی: **وجود ندارد**. تنظیمات حریم خصوصی تغییر نکرد.

## اصلاح رابط و شواهد

- علت تأییدشده: `select` در reset فونت نبود؛ provider/model با Arial 13.33px مقابل ورودی Vazirmatn 16px دیده شد.
  دستهٔ نمونه Vazirmatn 13.6px داشت. reset بومی و typography کنترل‌های فرم اصلاح شد؛ framework جدید نصب نشد.
- پس از اصلاح provider/model/category و ورودی/دکمهٔ کنارشان Vazirmatn 16px/weight400 دارند؛ کلید LTR می‌ماند و
  فرم/منو RTL است. شناسهٔ مدل در option با Unicode isolate و زیر منو با `bdi` کامل و قابل شکستن نمایش داده می‌شود.
- Chromium برای select تک‌خطی با وجود CSS line-height، مقدار computed `normal` برمی‌گرداند؛ کنترل native حفظ شد.
  ارتفاع واقعی provider/model حدود51.4px و دسته45px است؛ ورودی/دکمه line-height28px دارند. popup سیستم‌عامل را
  نمی‌توان در همهٔ پلتفرم‌ها با CSS یکسان کرد؛ دستگاه فیزیکی iOS/Android آزموده نشده است.
- تصاویر قبل: `artifacts/screenshots/typography-before-settings-{390,1440}.png` و
  `typography-before-category-390.png`. تصاویر بعد: `typography-after-{settings,model,category}-{390,1440}.png`.
  تصاویر موبایل مدل/دسته و تنظیمات دسکتاپ بازبینی بصری شدند؛ فقط مالک و متن مصنوعی و فرم کلید خالی دارند.
- آزمون RED واقعی Arial/اندازهٔ ناهماهنگ را ثبت کرد. در توسعهٔ harness، timeout بارگذاری، فرض نادرست وجود مدل دوم
  OpenAI و نیاز به تأیید brief قبل از دسته اصلاح شدند؛ آن اجراها موفق محسوب نشدند. انتظار line-height بومی نیز
  پس از مشاهدهٔ computed style به کنترل اندازه/ارتفاع واقعی اصلاح شد؛ رگرسیون خانواده/اندازهٔ فونت حفظ شده است.

## بررسی‌های اجراشده و عملیات

- `AssistantSettings.test.tsx`: **7/7** موفق، شامل خطای load، switching و duplicate/stale mutations.
- ESLint فایل تغییرکرده موفق؛ یک build تصویر web با TypeScript/Vite موفق. قبل از build فضای آزاد میزبان 1.7GiB،
  Docker پاسخ‌گو، فایل‌سیستم داخل کانتینر 918GiB آزاد و PostgreSQL ready بود. هیچ cleanup/volume operation انجام نشد.
- Backend: `docker compose exec -T -w /app/backend api python manage.py test tests.unit.test_provider_credentials tests.unit.test_gapgpt_copilot --settings=config.settings.test --keepdb --verbosity 1`
  نتیجه **9/9**، صفر failure/error/skip؛ transport ساختگی (از جمله SDK با MockTransport)، نه تماس GapGPT واقعی.
- NGINX واقعی در `http://127.0.0.1:58080`: credential-switch **2/2** موفق با مالک تازه و کلید مصنوعی/حذف همان کلید؛
  typography **2/2** موفق در 390 و1440، computed font، انتخاب keyboard/type-ahead، Escape/focus، مدل بلند و viewport.
  بازاجرای نهایی با tap روی خود select و Escape/focus در هر دو اندازه **2/2** موفق در1.5دقیقه بود؛
  touch فقط شبیه‌سازی مرورگر است. نتایج نامرتبط قبلی مجدداً اجرا نشدند.
- فقط web با `up -d --no-deps web` از overlay فعلی بازسازی شد. API/DB و keyring قبلی حفظ شدند؛ mount موجود و
  مقادیر مؤثر Django `mock / OFFLINE` بررسی شد. دستور canonical بدون تغییر:

```sh
COPILOT_MASTER_KEYRING_PATH=/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key bash scripts/dev-with-credentials.sh up -d
```

Spec Kit: FR-090/091 و T098–T100 اضافه شدند؛ analyze محدود پوشش2/2 الزام با3task، صفر مسئلهٔ بحرانی/تعارض قانون،
و gate صریح eligibility داشت. checklist موجود16/16، بدون hook ثبت‌شده. scoped implement فقط همین اصلاحات؛ نه
full-product convergence. hash نهایی commit و hash مشاهده‌شدهٔ remote در پاسخ تحویل گزارش می‌شود.

---

# اصلاح تنظیمات ارائه‌دهنده — 2026-11-16

مبنای این اصلاح: `9f9e254fdfa1342ccbe19bbbf536bc09f51ba10d`، شاخهٔ `002-personalized-shopping-copilot`.
تحویل نهایی این اصلاح شامل commit/push روی همین شاخه است؛ hash محلی و hash مشاهده‌شدهٔ remote در پاسخ تحویل
ثبت می‌شود. تحویل قبلی UX و شواهد اجرای قبلی در ادامه حفظ شده‌اند.

## تکمیل نهایی تنظیمات

- قفل هم‌زمان `ref` جلوی دو mutation پیش از render را می‌گیرد. generation مربوط به lifecycle تمام ادامه‌های
  async پس از خروج/reload را باطل می‌کند؛ پاسخ قدیمی نه credential منتشر می‌کند و نه قفل جدید را آزاد می‌کند.
  فرم فقط با provider منطبق قابل ذخیره/حذف است؛ هنگام تغییر یا حذف پاک و در خطا قابل بازیابی است.
- سه تست جدید پیش از اصلاح شکست واقعی داشتند: دو PATCH، دو PUT، و ادامهٔ GET پس از unmount.
  پس از اصلاح، suite متمرکز `AssistantSettings.test.tsx` هفت تست موفق دارد، شامل double-delete و مقصد OpenAI.
- ESLint دو فایل تغییرکرده موفق بود. تصویر web فقط یک‌بار برای کد جدید ساخته شد؛ TypeScript و Vite موفق.
  نتیجه‌های backend/فرانت‌اند نامرتبط قبلی استفاده شدند، نه اینکه اجرای تازه ادعا شود.
- اجرای اول مرورگر نهایی در دو اندازه هنگام بارگذاری تنظیمات timeout شد؛ هم‌زمان curl محلی نیز timeout داشت.
  بعداً API و gateway پاسخ 200 دادند، PostgreSQL آماده بود و بررسی محدود لاگ‌ها خطای storage/I/O نشان نداد.
  بار CPU سرویس‌های دیگر مشاهده شد ولی علت قطعی اعلام نشد؛ هیچ سرویس نامرتبط یا storage تغییر نکرد.
- بازاجرای همان `copilot-credential-switch.spec.ts` بدون تغییر assertionها: 2/2 موفق در 52.4 ثانیه، عرض‌های
  390 و1440 روی NGINX واقعی. هر تست browser context/مالک مهمان تازه، کلید ساختگی، reload و حذف خودش را داشت؛
  key/trace/video/screenshot واقعی ثبت نشد. شواهد run قبلی زیر با این اجرای تازه اشتباه نشوند.

فرمان‌های بررسی متمرکز این تحویل (node نسخهٔ 20.19.0 محلی):

```sh
# frontend/
node node_modules/vitest/vitest.mjs run src/features/copilot/memory/AssistantSettings.test.tsx --maxWorkers=1
node node_modules/eslint/bin/eslint.js src/features/copilot/memory/AssistantSettings.tsx src/features/copilot/memory/AssistantSettings.test.tsx
# repository root, after the single web build/recreation
NODE_PATH=$PWD/frontend/node_modules PLAYWRIGHT_BASE_URL=http://127.0.0.1:58080 node frontend/node_modules/@playwright/test/cli.js test --config frontend/playwright.config.ts tests/e2e/copilot-credential-switch.spec.ts --reporter=list
```

- API با فرمان canonical زیر و گزینه‌های `--no-deps --force-recreate api` دوباره ساخته شد؛ inspect وجود
  `/run/secrets/copilot_master_keyring` و بررسی `keyring()` دسترس‌پذیری رمزنگاری را تأیید کرد.
  کلید اصلی ساخته/تعویض یا چاپ نشد. startup یک‌بارهٔ بدون overlay و با `COPILOT_MASTER_KEY_FILE=` نیز
  `python backend/manage.py check` را با صفر مشکل گذراند؛ کانتینر اصلی دست‌نخورده در حالت دارای secret ماند.
- حالت مشاهده‌شده: AI=mock، research=OFFLINE، مجوز Phase12=false، نرخ تبدیل و همهٔ capها صفر؛ margin=0.15.
  هیچ provider call/purchase انجام نشد. OpenRouter فقط لینک اطلاعاتی است، نه گزینهٔ انتخاب یا اتصال آماده.
- Spec Kit: FR-088/089 به T093–T097 نگاشت دارند؛ T096 خارج تحویل و باز است؛ بررسی محدود تعارض بحرانی ندارد،
  checklist برابر 16 checked/0 unchecked و extension hook موجود نیست. T039 feature001 باز مانده است.

فرمان canonical از ریشه، با همان فایل موجود در این دستگاه:

```sh
COPILOT_MASTER_KEYRING_PATH=/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key bash scripts/dev-with-credentials.sh up -d
```

برای نصب آفلاین بدون ذخیرهٔ credential، `docker compose -f compose.yaml up -d` با AI mock و research OFFLINE
پشتیبانی می‌شود؛ آن را برای بازسازی کانتینری که باید ذخیرهٔ کلیدش فعال بماند استفاده نکنید.

### پیش‌نیازهای یک گفتگوی واقعی GapGPT — هنوز اجرا نشده

1. حساب دارای دسترسی/اعتبار کافی برای `gapgpt-deepseek-v4.1-flash`؛ ذخیرهٔ کلید GapGPT فقط در تنظیمات همان
   مالک مرورگر، با secret mount موجود. کلید واقعی این کاربر بررسی نشده است.
2. مجوز صریح جدید هزینه برای validation، گفتگو و retry؛ مبلغ پیشنهادی قبلی مجوز نیست. تنظیم
   `COPILOT_PHASE12_SPENDING_AUTHORIZED=1`، سقف کل `COPILOT_PHASE12_TOTAL_CAP_TOMAN`، نرخ تاریخ‌دار
   `COPILOT_USD_TO_TOMAN_RATE`، حاشیهٔ محافظه‌کارانه `COPILOT_EXCHANGE_MARGIN_RATIO` و سقف‌های مثبت و کافی
   `COPILOT_OPERATION_CAP_MICROUSD`، `COPILOT_SESSION_CAP_MICROUSD`، `COPILOT_DAILY_CAP_MICROUSD`.
   ledger قبلی/مصرف موجود حفظ شود؛ هیچ مبلغی در این تحویل مجاز یا reset نشده است.
3. پس از مجوز، اقدام صریح «بررسی صریح مدل‌های حساب» باید پاسخ واقعی معتبر بدهد و همان revision را VALIDATED کند؛
   این مرحله خودش تماس مولد قابل‌هزینه است، نه بررسی رایگان. تغییر دستی وضعیت دیتابیس ممنوع است.
4. فقط پس از این شروط، `COPILOT_AI_MODE=live` و بازسازی API با فرمان canonical؛ research همچنان OFFLINE.
   گفتگو متنی/مصنوعی بدون تصویر و دادهٔ حساس، با provider/model صریح و بدون fallback؛ clarification محلی
   را پاسخ مدل واقعی نشمارید. evidence تماس/usage/cost و پاسخ نهایی را ثبت کنید؛ کیفیت انسانی و انتشار عمومی gate جدا دارند.
   مدت دقیق نگه‌داری API نزد provider همچنان unresolved است؛ قبل از استفاده از دادهٔ شخصی باید روشن شود.

## نتیجهٔ اصلاح فعلی

- علت ذخیره‌نشدن کلید: کانتینر API فقط `/app` داشت و mount فایل رمزنگاری اصلی حذف شده بود.
  همان `/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key` با مجوز 0600 دوباره در
  `/run/secrets/copilot_master_keyring` mount شد؛ هیچ کلید اصلی/اعتبارنامهٔ واقعی تعویض یا خوانده و چاپ نشد.
- خطای جابه‌جایی: پس از موفقیت PATCH و شکست GET کلید، فرم ارائه‌دهندهٔ قبلی باقی می‌ماند.
  اکنون وضعیت کلید پاک می‌شود، فرم فقط برای provider منطبق نمایش/ارسال می‌شود و بازیابی تنظیمات ممکن است.
  پیام ذخیرهٔ موفق از فعال‌بودن اتصال زنده تفکیک شده است.
- `scripts/dev-with-credentials.sh` برای حفظ secret overlay در startupهای بعدی اضافه شد؛ دستور در README و
  `docs/backend-operations.md` آمده است. مسیر خالی، نسبی یا فایل ناموجود قبل از Docker رد می‌شود.
- راهنمای OpenRouter و لینک رسمی ساخت حساب/کلید در تنظیمات اضافه شد؛ **اتصال رایگان هنوز پیاده‌سازی نشده**.
  جزئیات مقایسهٔ OpenRouter/Groq و سؤال‌های لازم از پشتیبانی در
  `specs/002-personalized-shopping-copilot/free-provider-readiness.md` است. اجازهٔ ارائهٔ سرویس به کاربران/سرور
  ایران و قرارداد مدل رایگان/داده مشخص نشده؛ T096 باز است. کلید OpenRouter را در کادر OpenAI وارد نکنید.

## شواهد تازه

- تست regression ابتدا به‌علت باقی‌ماندن فرم قبلی شکست خورد؛ بعد از اصلاح موفق شد.
- Vitest: 8 فایل، 28 تست، همگی موفق؛ ESLint و TypeScript exit 0.
- build تصویر web با TypeScript/Vite موفق؛ فقط API با overlay و سپس web محلی بازسازی شدند؛ DB/volume دست‌نخورده.
- `copilot-credential-switch.spec.ts`: دو تست واقعی Chrome/NGINX در عرض 390 و1440 موفق: ذخیرهٔ کلید ساختگی
  OpenAI، جدایی کلید GapGPT، رفت‌وبرگشت provider، حفظ پس از reload، حذف کلید ساختگی.
  اجرای اول به‌علت locator دقیق label که متن optionها را نیز می‌خواند شکست خورد؛ با locator نقش combobox
  و نام دسترس‌پذیر صحیح اصلاح شد. assertionهای رفتار ضعیف نشده‌اند.
- تست مرورگر trace/video/screenshot ندارد؛ هیچ اعتبارنامهٔ واقعی وارد تست نشد. backend کد جدید ندارد؛
  سوئیت کامل قبلی دوباره اجرا نشد، ولی مسیر واقعی ذخیره/بازیابی/حذف از API و DB در تست مرورگر اجرا شد.
- Runtime: encryption available=true، AI=mock، research=OFFLINE. صفر تماس inference/validation با provider؛
  فقط مستندات عمومی برای تحقیق خوانده شد. هزینهٔ ارزیابی جدید صفر؛ مجوزهای هزینه reset نشده‌اند.
- بررسی Spec Kit محدود: FR-088/089 به T093–T096 نگاشت شدند؛ تناقض بحرانی صفر؛
  checklist موجود 16 checked/0 unchecked، extension hook موجود نیست. T039 feature001 و تمام gateهای live/public بازند.
- حذف نامرتبط `test.txt` و چهار screenshot از قبل دست‌نخورده‌اند؛ secret، dump یا runtime artifact به Git افزوده نشده.

---

# تحویل بازطراحی محدود UX — Beforebuy

تاریخ: 2026-11-16؛ شاخه: `002-personalized-shopping-copilot`.
مبنای شروع: `94c63db0332785d4ed86a4aab56ddcae0864ed4a`.
تحویل قبلی: `docs/archive/phase-12-handoff.md`. پذیرش طراحی توسط مدیر محصول یا تکمیل کل محصول ادعا نمی‌شود.

## تجربهٔ جدید

- صفحهٔ اصلی `http://127.0.0.1:58080/` و `/copilot`؛ نسخهٔ قبلی `/legacy`.
  لینک‌های `/?analysis=<id>` و `/?view=history` و API/مالکیت قبلی حفظ شدند؛ NGINX موجود SPA fallback دارد.
- اولین پیام گفتگو می‌سازد. شش دسته و مثال‌های متنوع شروع گفتگو هستند، نه وعدهٔ پوشش بازار.
- Concept 2: زمینهٔ گرم، Vazirmatn محلی، SVG، گفتگوی راست و میز انتخاب چپ؛ نمایش تدریجی نیاز، گزینه، مقایسه و پیشنهاد فروش.
- composer خط مبنا در 1280×720 تا y=774 بیرون می‌رفت. اکنون پیمایش thread/desk مستقل و composer چندخطی محدود است؛ ارسال/توقف در پنجرهٔ کوتاه و موبایل در دسترس‌اند.
  محفظهٔ responsive مشکل zoom را حل می‌کند؛ overflow سراسری برای پنهان‌کردن اشکال اضافه نشد.
- دنبال‌کردن فقط نزدیک انتهای گفتگو، حفظ محل خواندن و «پیام‌های جدید»؛ draft/scroll/research وابسته به گفتگو، جداسازی subscription/timer هنگام جابه‌جایی.
- پاسخ اختیاری دسته/مخاطب/تأیید یا حفظ بودجه/تأیید یا اصلاح نیاز از مسیر عادی پیام و idempotency عبور می‌کند.
  سؤال، conversation و revision کنترل می‌شوند؛ تأیید دستی جدید نیز گزینه/پرسش قدیمی را باطل می‌کند.
- «بودجه‌ام ۱۵ میلیون تومان است» user-reported و هنوز تأییدنشده ثبت می‌شود؛ «۱۵ میلیون ریال» پیشنهاد ۱٫۵ میلیون تومان است، نه بازنویسی خاموش ۱۵ میلیون.
  تأیید یا حفظ مبلغ داخل گفتگو انجام می‌شود؛ ۱۰ ریال = ۱ تومان. parser محدود است، نه درک عمومی زبان طبیعی.
- تاریخچه: جستجوی صادقانه فقط در عنوان‌های بارگذاری‌شده، تاریخ، pagination، بازکردن/تازه، حذف تک و پاک‌کردن همه با تأیید.
  حافظهٔ مشتق‌شده حذف می‌شود؛ credential، تنظیمات مستقل و حسابداری حفظ می‌شوند؛ undo ادعا نمی‌شود.
- race پاسخ REST قدیمی با پیام نهایی و race توقف با پایان عملیات اصلاح شد؛ وضعیت واقعی سرور ملاک است.

## حالت اجرا

AI برابر `mock` و پژوهش `OFFLINE` باقی ماند. UI حالت مؤثر، provider/model و وضعیت ذخیره/اعتبارسنجی credential را از backend می‌گیرد.
پیش‌فرض نشست تازه GapGPT / `gapgpt-deepseek-v4.1-flash` است؛ انتخاب موجود کاربر یا کلید OpenAI تغییر، منتقل، چاپ یا اعتبارسنجی نشد.
کلید OpenAI نشانهٔ تنظیم GapGPT نیست؛ gate منطقه‌ای دور زده نشد. فراخوانی زندهٔ provider/منبع، هزینه، خرید و deployment عمومی این فاز: صفر.

## حفاظت داده و rollback

migration افزایشی `0017_conversational_ux` اعمال شد. قبل از آن API متوقف و backup محافظت‌شده تهیه شد:
`/Users/mehdi/Backups/beforebuy/ux-redesign-7fUJFR/pre-ux.dump`
پوشه 0700، فایل 0600، اندازه 276705 بایت؛ SHA-256:
`41f9d49f10167083af29c46b059aec16fffd48689f86a1274879d230ac082b6a`.
`pg_restore --list` موفق، خروجی 241 خط؛ این بررسی خوانایی است نه restore rehearsal.
volume `beforebuy_beforebuy_pgdata_v18` و داده‌های موجود حفظ شدند؛ backup خارج Git/Trash باقی می‌ماند.
rollback رابط: frontend قبلی با schema افزایشی حفظ‌شده. rollback DB فقط به volume تازه پس از توقف نوشتن و بررسی restore/حسابداری؛ هرگز بازنویسی volume فعال.

## شواهد تأیید

- backend: `./scripts/test-backend.sh --keepdb --verbosity 1`، ۳۲۰ کشف/اجرا/موفق؛ صفر skipped/failure/error و system check پاک.
- Playwright روی NGINX واقعی: ۷/۷ موفق در ۳٫۲ دقیقه؛ چهار اندازهٔ 1440×900، 1280×720، 390×844 و 360×640، دو regression مقایسه و یک مسیر بلند/legacy. صفر failure/skipped؛ axe serious/critical صفر در بررسی‌های اجراشده.
- React: `vitest run --maxWorkers=1`، ۲۶/۲۶ موفق در ۸ فایل؛ lint موفق.
- `docker compose build web`: typecheck و Vite موفق؛ `makemigrations --check --dry-run`: بدون تغییر.
- YAML قراردادها خوانده شد؛ `git diff --check` پاک بود.
- تست‌های قرمز بودجه، سؤال قدیمی، refresh، Escape، zoom و توقف قبل از اصلاح مشاهده شدند.
  یک timeout پنج‌ثانیه‌ای در اجرای پربار فرانت‌اند و انتظار اشتباه رشتهٔ خالی به‌جای null در تست backend اصلاح/بازاجرا شدند؛ شکست‌ها موفق شمرده نشده‌اند.
  فرض نادرست لغو همیشگی پاسخ بسیار کوتاه با بررسی دقیق 200/CANCELLED یا 409/OPERATION_TERMINAL و وضعیت واقعی COMPLETED جایگزین شد؛ انتظار پایان handler هنگام unroute، خطای ابزار «Route is already handled» را رفع کرد. اجرای میانی متوقف‌شده موفق شمرده نشد؛ اجرای کامل نهایی هر هفت مورد را گذراند.
- تصاویر مصنوعی: `artifacts/screenshots/ux-home-{1440,1280,390,360}.png`،
  `ux-chat-{1440,1280,390,360}.png`، `ux-comparison-{1440,390}.png`؛ تصاویر دسکتاپ/موبایل بصری بازبینی شدند.
- مرورگر واقعی NGINX: چهار اندازهٔ خواسته‌شده، thread بلند، تاریخچهٔ ۵۳تایی، جابه‌جایی هنگام stream، بودجه/پاسخ دلخواه،
  تنظیمات/پروفایل و draft، کاهش ارتفاع، keyboard/focus، reduced motion، axe، zoom و گزارش legacy.
  تأخیر کنترل‌شده فقط تحویل SSE به مرورگر است، نه اندازه‌گیری latency مدل.
- صفحه‌کلید فیزیکی موبایل، دستگاه واقعی و zoom بومی مرورگر آزمایش نشد؛ CSS zoom و کاهش viewport معادل آن‌ها نیست.
  کیفیت مدل/بازار زنده و عبور همهٔ suiteهای تاریخی مرورگر ادعا نمی‌شود؛ HTTPهای provider در backend stub هستند.

## Spec Kit و ابزار

FR-082–087 به T086–T092 نگاشت دارند؛ analyze غیرمخرب محدوده: ۶ الزام، ۷ تسک، پوشش ۱۰۰٪، تعارض بحرانی صفر.
implement محدود به همین فاز بود. مهارت‌های موجود project، frontend-design، Django/DRF، TDD، systematic-debugging،
Playwright، verification و Spec Kit استفاده شدند؛ ابزار/مهارت تازه نصب نشد و snapshotهای غیرفعال فعال نشدند.
feature001 T039، T066، gateهای live/human و Milestone E باز می‌مانند.

## مرور پنج‌دقیقه‌ای

۱. صفحهٔ اصلی: «گوشی من شکسته، می‌خواهم آیفون ده بخرم.»
۲. سپس «بودجه‌ام ۱۵ میلیون تومان است» و «۱۵ میلیون ریال»؛ پیشنهاد تغییر را تأیید یا مبلغ قبلی را حفظ کنید.
۳. یک پاسخ پیشنهادی، سپس کاربرد با متن خودتان و تأیید نیاز؛ نمونهٔ آموزشی مقایسه اختیاری و صریحاً مصنوعی است.
۴. پیش‌نویس بنویسید، تنظیمات/شناخت من را باز و برگردید؛ تاریخچه را جستجو و فقط گفتگوی آزمایشی خود را با تأیید حذف کنید.
۵. پنجرهٔ کوتاه/موبایل، پیمایش متن بلند و «نسخهٔ قبلی» با گزارش قبلی را امتحان کنید. هیچ اعتبارسنجی کلید لازم نیست.

## Git

نتیجهٔ commit/push و hash دقیق در پاسخ تحویل ثبت می‌شود؛ فقط تغییرات مرتبط مجازند.
حذف نامرتبط `test.txt` و چهار تصویر قدیمی phase8/phase9-2 خارج commit و در working tree محفوظ‌اند.
هیچ secret، dump، trace مرورگر، دیتابیس یا runtime artifact وارد Git نمی‌شود.
