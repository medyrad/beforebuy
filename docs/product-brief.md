# خلاصه محصول

## جهت مصوب Personalized Shopping Copilot

Beforebuy اکنون به‌عنوان دستیار شخصی خرید چنددسته‌ای تعریف می‌شود: کاربر در گفت‌وگوی فارسی/RTL مسئله، بودجه،
کاربرد، محدودیت و recipient را روشن می‌کند؛ سپس پژوهش on-demand و محدود، evidence قابل‌ردیابی و «میز انتخاب»
برای مقایسهٔ گزینه‌ها دریافت می‌کند. هدف همچنان informed choice و کاهش ابهام است، نه افزایش خرید یا بودجه.

- تجربهٔ اصلی conversation-first است و پرسش‌نامهٔ ثابت تلفن feature 001 مسیر legacy محسوب می‌شود.
- پوشش UI چنددسته‌ای با data readiness هر category یکی نیست؛ electronics، home appliance و sports/fashion فقط
  سه contract/fixture نماینده‌اند تا هرکدام source gate مستقل داشته باشند.
- Choice Desk ranking، total payable cost، hard constraint، tradeoff، evidence coverage و unknown را کنار هم نشان
  می‌دهد. arithmetic/filter/rank قطعی از rule نسخه‌دار است و LLM authoritative نیست.
- memory فقط opt-in است؛ preference صریح، inferred candidate و self/gift/household context جدا می‌مانند.
- runtime جدید direct OpenAI Responses و user-owned API key را هدف می‌گیرد، اما key eligibility یا region support
  را ثابت نمی‌کند. با کاربران/backend ایران activation تا پشتیبانی رسمی blocked است.
- research bounded است؛ bypass، crawl انبوه، checkout، affiliate optimization و price alert خارج scope هستند.
- معماری React + Vite، Django/DRF، PostgreSQL، same-origin، Compose و تک‌سرور حفظ می‌شود.

Specification canonical این جهت در `specs/002-personalized-shopping-copilot/` است. feature 001 و داده/شواهد آن تا
تصمیم cutover حفظ می‌شوند و `T039` آن همچنان pending است. Milestone A پیاده شده است. Phase 9 زیرساخت evidence و
پژوهش محدود Milestone B را با حالت پیش‌فرض `OFFLINE`، fixtureهای صریح و safe-fetch مستقل پیاده کرد، اما هیچ منبع live
به‌دلیل ابهام permission/retention/display فعال نیست و پوشش sports همچنان باز است. Phase 10 میز انتخاب قطعی را
با evidence/fixture پیاده کرد. Phase 11 تنظیمات قابل‌مشاهده، کلید رمز‌شده و حافظهٔ opt-in را پیاده و با دادهٔ مصنوعی
آزمود؛ adapter مستقیم OpenAI فقط stub-tested است. پوشش بازار زنده، فعال‌سازی AI و انتشار عمومی همچنان بازند.

## مسئله و ارزش پیشنهادی

Purchase Regret Predictor یک دستیار مستقل برای تصمیم خرید است. پرسش محوری آن این است: «آیا این خرید با نیازها و شرایط من منطقی است؟» ارزش محصول در افزایش خرید نیست؛ در روشن‌کردن تناسب نیاز، فشار بودجه، توجیه تعویض دستگاه فعلی، نگرانی‌ها، ابهام‌ها و گزینه‌های جایگزین است.

این محصول ادعای پیش‌بینی علمی یا اعتبارسنجی‌شده‌ی پشیمانی آینده را ندارد. خروجی باید تصمیم‌یار و توضیح‌پذیر باشد و محدودیت شواهد را صریح بیان کند.

## مخاطب و مسیر پیشنهادی

مخاطب پیشنهادی فرد فارسی‌زبانی است که برای خرید یا تعویض تلفن همراه مردد است و می‌خواهد پیش از تصمیم، نیازها و محدودیت‌های خود را منظم بررسی کند. این تعریف یک فرض اولیه است و هنوز با research معتبر تأیید نشده است.

مسیر پیشنهادی کاربر:

1. مدل تلفن موردنظر و قیمت تقریبی را دستی وارد می‌کند.
2. شش سؤال کوتاه درباره وضعیت دستگاه فعلی، نتیجه مورد انتظار، استفاده، فوریت، بودجه و tradeoff تکمیل می‌کند.
3. در صورت وجود ابهام، حداکثر سه پرسش روشن‌کننده‌ی AI دریافت می‌کند.
4. گزارش تصمیم‌یار توضیح‌پذیر را می‌بیند.
5. بعداً تحلیل‌های قبلی را باز می‌کند و بازخورد ساده‌ی مفیدبودن می‌دهد.

## MVP تاریخی feature 001

- فقط تلفن همراه.
- رابط فارسی با پشتیبانی RTL و دسترس‌پذیری.
- ورود دستی تلفن موردنظر و قیمت تقریبی.
- پرسش‌نامه با دو field محصول و شش core question؛ مسیر عادی ۸ primary input field و طولانی‌ترین مسیر حداکثر
  ۱۱ question/input prompt از یک pool مشترک سه follow-up دارد. این‌ها count field/prompt هستند، نه user action.
- گزارش categorical به‌طور جداگانه justification خرید/تعویض، budget fit و suitability نامعلوم/گزارش‌شده‌ی
  مدل هدف را نشان می‌دهد؛ Purchase Fit Score عددی deferred است.
- history مهمان در همان browser، حذف یک analysis و پاک‌کردن همه history؛ بدون cross-device recovery یا
  public sharing در first slice.
- usefulness feedback اختیاری ۱ تا ۵ برای هر report revision جاری؛ قابل تغییر/حذف و بدون explanation/contact.

شکل دقیق score، ابعاد، وزن‌ها، thresholdها و مدیریت uncertainty هنوز تصمیم‌گیری نشده است. score نباید پیش از specification و testable business rules پیاده‌سازی شود و LLM نباید آن را به‌طور authoritative بسازد.

## refinement مربوط به Phase 1 و تصمیم‌های Phase 1.1

این refinementها جهت supplied by product lead هستند، نه finding حاصل از user research:

- گزارش first slice conclusionهای budget fit، purchase/replacement justification و target-model fit را مستقل
  نگه می‌دارد؛ tradeoffها نیز جدا گزارش می‌شوند و report mode metadata مربوط به feedback است.
- categorical outcomes و rubric دقیق `PDA-CAT-v0.3` در M1 پیاده و برای integration پذیرفته شده‌اند. Purchase Fit
  Score عددی حذف نشده، اما تا weight/threshold قابل دفاع deferred است؛ Phase 4 فقط رابط M2 را مجاز می‌کند.
- evidence از `USER_REPORTED`، `DETERMINISTICALLY_DERIVED`، `VERIFIED_EXTERNAL` و `UNKNOWN` تفکیک می‌شود.
  در first slice هیچ external product fact verified وجود ندارد.
- اگر AI fail شود و rule deterministic قابل اجرا باشد، proposal یک report محدود و صریحاً rule-based همراه
  retry state است؛ fabricated narrative نمایش داده نمی‌شود.
- real AI integration پیش از live-ready نامیدن MVP لازم است؛ mock فقط development/test را پشتیبانی می‌کند.
- retention pilot برابر ۹۰ روز از اولین report persistشده، non-sliding و با active purge target حداکثر ۲۴
  ساعت پس از expiry تایید شده است. edit/retry/visit/feedback anchor را reset نمی‌کنند.
- feedback metric فقط average ratingهای retained همراه response count و report mode است؛ کاهش regret یا
  causal purchase outcome را اندازه‌گیری‌شده ادعا نمی‌کند.

## محدودیت‌ها و اصول محصول

- اطلاعات مفقود با evidence منفی یکسان نیست.
- مشخصات محصول و قیمت جاری نباید ساخته یا حدس زده شوند.
- انگیزه خرید مبنای تشخیص روان‌شناختی کاربر نیست.
- AI می‌تواند متن را تفسیر، ابهام را آشکار و evidence را توضیح دهد؛ scoring authoritative باید deterministic باشد.
- داده شخصی باید حداقلی باشد؛ فقط latest required answer/report state نگه‌داری می‌شود و logical revision ID
  ownership نتیجه و rating را روشن می‌کند. backup lifecycle پیش از production readiness باید مشخص شود.

## خارج از دامنهٔ feature 001 (historical)

- فروشگاه، checkout، پرداخت و affiliate monetization.
- scraping خودکار فروشگاه‌ها.
- آموزش مدل اختصاصی.
- اپلیکیشن native موبایل.
- recommendation engine چنددسته‌ای گسترده.
- Redis، Celery، Kubernetes، microservices، vector database یا agent orchestration بدون نیاز تصویب‌شده.

## فرض‌ها و نیازهای اعتبارسنجی

- وجود مسئله و تمایل مخاطب به تکمیل این جریان هنوز با user research اثبات نشده است.
- ارزش محدودشدن به تلفن همراه، questionnaire کوتاه و ساختار گزارش همچنان نیازمند validation با usage واقعی است.
- usefulness واقعی score و indicator کیفی باید با کاربران و مثال‌های واقعی ارزیابی شود.
- تحمل کاربر نسبت به پرسش‌نامه، اعتماد او به توضیحات و نیاز واقعی به history باید سنجیده شود.
- منبع external product data در first slice وجود ندارد؛ provider/model/limits تا AI integration deferred و
  backup lifecycle تا deployment readiness باز است. rubric blocker planning نیست.
