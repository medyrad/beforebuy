# تحویل Phase 12 — مسیر واقعی و provider-neutral دستیار خرید

تاریخ: 2026-11-15؛ branch: `002-personalized-shopping-copilot`؛ baseline:
`16fa0f8d655590ea03e13b2ca2c48251feedd20f`. حالت پیش‌فرض AI همچنان `mock` و پژوهش `OFFLINE` است.
فراخوانی واقعی provider، token مصرف‌شده، هزینه، خرید اعتبار، پیام به provider و deployment عمومی: **صفر**.

## تصمیم و شواهد provider

فقط GapGPT و AvalAI با منابع رسمی مقایسه شدند. GapGPT با مدل دقیق
`gapgpt-deepseek-v4.1-flash` انتخاب شد، چون صفحهٔ رسمی آن hosting/processing داخل ایران و Chat Completions streaming
روی endpoint ثابت را اعلام می‌کند. tariff رسمی: ورودی 0.15، cached input برابر 0.015 و خروجی 0.60 دلار به‌ازای هر
میلیون token. این‌ها ادعای provider هستند؛ کیفیت فارسی، latency، availability و invoice در workspace اندازه‌گیری
نشده‌اند. JSON Schema، tool calling، Responses و image input برای این مدل مستند نشده و در adapter ادعا نمی‌شوند.

AvalAI fallback پیشنهادی است، نه fallback خودکار: Responses/Chat Completions مستند است، اما مدل routed مشخص، upstream
eligibility کاربران ایران، data path/retention و tariff همان مدل باید دوباره روشن شود. minimum top-up/API credit هر دو
گزینه حل‌نشده است و هیچ ثبت‌نام یا خریدی انجام نشد. منابع مستقیم و ابهام‌ها در `provider-readiness.md` و `research.md`
ثبت شده‌اند.

## پیاده‌سازی

- migration افزایشی `0016` provider/model را صریح، credential جدید GapGPT را provider-bound و provider هر operation
  را pin می‌کند. ciphertext قدیمی OpenAI دست‌نخورده می‌ماند؛ تغییر/حذف credential عملیات وابسته را باطل می‌کند.
- factory جدید بر اساس `CopilotSettings.provider` انتخاب می‌کند. OpenAI مستقیم همچنان region-blocked است؛ arbitrary
  base URL یا reinterpretation کلید وجود ندارد. GapGPT فقط fixed Chat Completions و model allowlist دقیق را می‌پذیرد.
- پاسخ مدل JSON متنی bounded است و server آن را strict اعتبارسنجی می‌کند. acknowledgement و حداکثر یک سؤال طبیعی
  فارسی مجازند. تغییر brief فقط از دادهٔ گزارش‌شدهٔ کاربر پیشنهاد می‌شود و هرگز خودکار اعمال/تأیید نمی‌شود. قیمت،
  رتبه، مشخصات و factual block فقط از renderer قطعی و evidence جاری می‌آیند؛ current-market با research خاموش unknown است.
- worker/SSE، ownership، expiry، cancellation، context fingerprint، stale-publication guard و limited fallback حفظ شدند.
  retry حداکثر دو attempt است؛ usage موجود ثبت و usage غایب با reservation محافظه‌کارانه حساب می‌شود.
- UI فارسی provider/model/state و credential جدا را نشان می‌دهد. خواندن/ذخیره/حذف/تغییر provider هیچ provider call
  ندارد. explicit validation تنها با کلیک کاربر و پس از مجوز هزینه ممکن است.

## gate هزینه و فعال‌سازی

مجوز تاریخی AvalAI قابل استفادهٔ مجدد نیست. پیشنهاد جدید (هنوز **تأییدنشده**) سقف کل 50,000 تومان برای validation،
سناریوها و retryهاست. قبل از call باید همان سقف به‌طور صریح تأیید، نرخ تاریخ‌دار USD→toman ثبت و margin محافظه‌کارانه
15% و capهای operation/session/deployment مثبت شوند. authorization ID پایدار `phase12-gapgpt-live`، reserved+estimated
cost را پیش از transport قفل می‌کند. estimate تضمین invoice نیست.

پس از مجوز: master keyring موجود را mount، کلید GapGPT را فقط در UI محلی وارد، تنظیمات فوق را پیکربندی و سپس یک‌بار
«بررسی صریح مدل‌های حساب» را اجرا کنید. چون GapGPT probe رایگان مستند نکرده، این action یک generation کم‌حجم، bounded
و ledger-accounted انجام می‌دهد؛ تنها پاسخ معتبر همان model/revision را `VALIDATED` می‌کند. state را دستی تغییر ندهید.
در وضعیت تحویل، `COPILOT_PHASE12_SPENDING_AUTHORIZED=0` و همهٔ capها صفرند، پس مسیر fail-closed است.

## verification

- Spec Kit analyze غیرمخرب: FR-076 تا FR-081 به T078–T085 نگاشت دارند؛ placeholder، requirement بدون task و
  conflict بحرانی قانون اساسی پیدا نشد و checklist برابر 16/16 باقی ماند.
- TDD اولیه با missing module/model شکست خورد و بعد سبز شد. تست‌های متمرکز credential، GapGPT adapter، factory،
  model refresh و OpenAI regression شامل endpoint/model ثابت، نبود schema claim، JSON/fact rejection، brief proposal،
  transient retry، missing usage، stale operation، hard total cap، zero-call save و validation transport stubbed است.
- canonical backend: **۳۱۲/۳۱۲ موفق**، صفر failure/error؛ system check پاک. اجرای نخست کامل دو regression در تست‌های
  legacy OpenAI یافت که provider را صریح نمی‌فرستادند؛ association تست و invalidation provider-specific اصلاح شد و
  rerun کامل سبز شد. `makemigrations --check --dry-run` بدون drift بود.
- frontend: **۲۱/۲۱ در ۷ فایل**؛ typecheck و lint موفق. build محلی و Docker web (`tsc -b` + Vite) موفق بودند. اجرای
  نخست `npm` به‌علت باینری Hermes/libc++ قبل از test متوقف و build ترکیبی نخست در مرز ابزار قطع شد؛ هیچ‌کدام موفق
  شمرده نشدند و runtime pin‌شده/inspect سپس run کامل و قابل‌بررسی داد.
- migration `0016` روی PostgreSQL توسعه اعمال شد؛ DB/API/web سالم و volume حذف/reset نشد. Playwright واقعی پشت NGINX:
  **۱/۱ موفق**؛ provider/model GapGPT دیده شد، validation بدون credential قبل از transport متوقف و یک پیام فارسی آزاد
  در مسیر mock/SSE کامل شد. screenshot یا trace حاوی credential ساخته نشد.
- همهٔ HTTPهای provider در تست با MockTransport/stub بوده‌اند. live call count و actual cost هر دو صفر است.

## وضعیت باز

T078–T085 از نظر spec/implementation/verification تکمیل‌اند. T066، feature001 T039، source coverage، live Persian human review،
provider retention clarification، target-host release gate و public release باز می‌مانند. Milestone E/full-product
convergence ادعا نمی‌شود. حذف نامرتبط `test.txt` و چهار screenshot قدیمی Phase8/9.2 خارج commit حفظ می‌شوند.
