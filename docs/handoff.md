# تحویل Phase 11.1 — دستیار خرید context-aware

**Context assembly, validated shopping answers, meaningful streaming and synthetic UI demos implemented;
live OpenAI and public research remain disabled.**

تاریخ: 2026-11-15؛ branch: `002-personalized-shopping-copilot`؛ baseline:
`1ba303c00b1f61944fd0a0295dee4bf9d9a3d7fc`. تماس provider/public source، مصرف پولی و deployment عمومی: **صفر**.
AI روی `mock` و research روی `OFFLINE` باقی ماند. Milestone E شروع نشد.

## دامنه و Spec Kit

T071–T077 به feature موجود افزوده شدند. requirements/plan/data model، OpenAPI، personalization، stream contract،
OpenAI readiness و decisions با FR-069–FR-075 هم‌راستا شدند. analyze غیرمخرب: ۷ requirement جدید و سه scenario جدید
به T071–T077 نگاشت کامل دارند؛ ambiguity/duplicate/placeholder/constitution conflict بحرانی صفر و checklist برابر
16/16 است. feature001 T039، T066، T042–T048/T050 و gateهای live/release همچنان pending هستند.

## پیاده‌سازی

- `copilot_context.py` یک payload موقت و bounded از turn جاری، تاریخچهٔ محدود، brief، ChoiceSet جاری، هزینه/unknown،
  provenance ساختاریافته، upload واجد شرایط و فقط حافظهٔ confirmed/consented مرتبط می‌سازد. معیار صریح brief بر حافظه
  مقدم است؛ temporary و memory-disabled حافظه را حذف می‌کنند. critical context بیش‌ازحد، قبل از transport پاسخ محدود می‌دهد.
- migration افزایشی `0015` فقط manifest/fingerprint غیرمحرمانه را به StreamOperation اضافه می‌کند. manifest متن پیام،
  پروفایل یا source را تکرار نمی‌کند. turn/brief/generation/settings/model/ChoiceSet/snapshot/upload/memory هنگام هر delta و
  final دوباره بررسی می‌شوند؛ تغییرشان publication دیرهنگام را با `CONTEXT_STALE` قطع می‌کند.
- schema provider اکنون answer plan محدود است، نه clarification-only یا متن factual آزاد. candidate/criterion/evidence ID،
  value، attribution، freshness و source membership پیش از renderer قطعی فارسی اعتبارسنجی می‌شوند. block بدون شاهد حذف
  و به محدودیت صریح تبدیل می‌شود؛ ranking، قیمت، arithmetic و facts همچنان از pipeline deterministic می‌آیند.
- stream ابتدا `PROVISIONAL_CONTEXT` ایمن و سپس فقط `VALIDATED_BLOCK` server-rendered می‌دهد. raw JSON/hidden reasoning
  منتشر نمی‌شود؛ مسیر OpenAI delay مصنوعی typing ندارد. پیام persisted نهایی authoritative است.
- mock محلی از همان assembler/validator/worker/event ledger/publication استفاده می‌کند و `DEVELOPMENT_CONTEXT_FIXTURE`
  برچسب دارد. این مسیر فهم زبان یا کیفیت مدل زنده را اثبات نمی‌کند.
- `sdk_model_ids()` واقعاً SDK 3.49.0 `client.models.list()` را صدا می‌زند و با MockTransport آزموده شد. endpoint صریح
  `POST /api/v1/copilot/models/refresh` قبل از credential/transport eligibility را بررسی می‌کند؛ در ایران
  `REGION_BLOCKED` است. GET/PATCH settings و credential read/write هیچ discovery ندارند.

## سه گفت‌وگوی مصنوعی قابل نمایش

1. electronics، بودجه ۱۰٬۰۰۰٬۰۰۰، intended «رایانهٔ نمایشی آ»، سؤال «چه جایگزینی در همین مقایسه داری؟»؛ پاسخ:
   «رایانهٔ نمایشی پ» جایگزین پشتیبانی‌شده با هزینهٔ نهایی ۹٬۰۰۰٬۰۰۰ تومان.
2. electronics با intent لذت/پاداش، شرط قطعی portable=true، intended «رایانهٔ نمایشی ب»، سؤال «چرا این گزینه با نیاز من هم‌خوان نیست؟»؛
   پاسخ mismatch قابل‌حمل‌بودن فقط با evidence همان candidate/source.
3. sports، شرط قطعی waterproof=true، intended «کفش نمایشی پ»، سؤال «برای تصمیم چه چیزی هنوز نامعلوم است؟»؛ پاسخ:
   ضدآب‌بودن نامعلوم است و باید از منبع معتبر بررسی شود؛ ادعای «ضدآب است» ساخته نمی‌شود.

مسیر بازتولید کامل در `quickstart.md` است. screenshots مرتبط:
`copilot-phase11-1-{alternative,mismatch,unknown}.png`. تصاویر قدیمی Phase8/9.2 نامرتبط stage نمی‌شوند.

## verification واقعی و شکست‌های ثبت‌شده

- TDD متمرکز context/answer/adapter/model refresh/worker، شامل overflow کل context و سقف سه block، موفق. worker واقعی phaseهای safe/validated را نوشت و
  تغییر settings پیش از final با `CONTEXT_STALE` و بدون final message متوقف شد.
- canonical backend روی HEAD نهایی: **۳۰۰/۳۰۰ موفق**؛ صفر failure/error؛ system check پاک.
  `makemigrations --check --dry-run` بدون drift. HTTPهای 200/401 SDK فقط MockTransport هستند، نه تماس provider.
- frontend: **۲۱/۲۱ در ۷ فایل**؛ typecheck و lint موفق. Docker web build (`tsc -b` + Vite) موفق؛ migration 0015 روی
  PostgreSQL توسعه اعمال شد؛ API/DB/web پس از restart سالم و volume/data حذف یا reset نشد.
- Playwright واقعی پشت NGINX: سه conversation بالا در یک worker موفق شدند و screenshot تولید شد. refresh مدل در UI
  نیز region block قابل‌مشاهده نشان داد و هیچ transportی اجرا نکرد.
- اجرای نخست Vitest به‌علت Node خراب `~/.local/bin`/Hermes قبل از test متوقف شد؛ با Node 20.19.0 pin‌شده اجرا شد.
  اجرای نخست Playwright یک import harness failure داشت. سپس یک assertion strict چندقیمتی و انتخاب‌نشدن صریح دستهٔ
  fixture ورزشی شکست خورد؛ علت‌ها اصلاح و rerunهای موفق جدا ثبت شدند. هیچ شکست اولیه موفق شمرده نشده است.

## محدودیت‌ها و gateهای باز

هیچ live OpenAI call، account model listing، کیفیت فارسی، latency، invoice یا source coverage اندازه‌گیری نشده است.
`models.list()` فقط seam stubbed است؛ ID حساب به‌تنهایی capability/price/retention را ثابت نمی‌کند. validation ساختاریافته
می‌تواند ID/value/provenance جاری را enforce کند، اما semantic entailment آزاد و prompt injection عمومی را حل‌شده ادعا
نمی‌کنیم؛ به همین دلیل renderer factual آزاد وجود ندارد. context محدود است و تاریخچهٔ قدیمی ممکن است با marker حذف شود.

فعال‌سازی آینده نیازمند eligibility رسمی برای کاربران/سرور ایران، credential validated، account-model intersection،
مجوز مستقل هزینه و live evaluation، review retention/key operations، source coverage و target-host/release rehearsal است.
T066 و feature001 T039 باز می‌مانند؛ full-product convergence ادعا نمی‌شود.

## Git و فایل‌های محلی

فقط کد، migration، تست، Spec Kit docs، operations/quickstart/handoff و سه screenshot جدید Phase11.1 مرتبط باید commit
شوند. حذف نامرتبط `test.txt` و چهار screenshot قدیمی Phase8/9.2 خارج commit می‌مانند. secret، key، backup، DB، log،
trace، cache، `.env` و runtime artifact وارد Git نمی‌شوند. hash و نتیجهٔ push در گزارش نهایی اعلام می‌شود.
