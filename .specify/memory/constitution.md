# Beforebuy Shopping Copilot Constitution

## Core Principles

### I. Lean Evidence-Bounded Scope

هر feature MUST یک نیاز تأییدشده یا acceptance criterion مشخص را پاسخ دهد. پوشش چنددسته‌ای، گفت‌وگو،
research و recommendation فقط در milestoneهای محدود و مستقل گسترش می‌یابد؛ interface coverage نباید با source
coverage یا recommendation readiness یکی فرض شود. dependency، service، abstraction و infrastructure جدید فقط با
نیاز concrete، گزینه‌های بررسی‌شده، license سازگار و هزینه عملیاتی ثبت‌شده مجاز است. Redis، Celery، Kubernetes،
microservice، vector database، distributed crawler، browser fleet و agent orchestration بدون نیاز و measurement مصوب
ممنوع‌اند.

### II. Traceable Requirements and Acceptance Criteria

هر تغییر رفتاری MUST به feature specification و acceptance criteria قابل آزمون قابل ردیابی باشد. تصمیم مصوب،
proposed default، assumption، measured result و open question MUST جدا ثبت شوند و assumption نباید بدون تصمیم صریح
به requirement تبدیل شود. تغییر consequential MUST اسناد، contractها و specificationهای متاثر را در همان change
به‌روزرسانی کند. written acceptance scenario به‌تنهایی test اجراشده نیست.

### III. Deterministic Constraints, Arithmetic and Ranking

بودجه، واحد پول، total payable cost، compatibility، hard filter، variant identity و هر score، weight، threshold یا
ترتیب قطعی MUST از ruleهای مشخص، نسخه‌پذیر، explainable و testable به دست آیند. LLM MUST NOT arithmetic، product fact،
price، availability، seller trust، popularity یا score authoritative بسازد. recommendation subjective MUST با معیار،
evidence، tradeoff، uncertainty و شرایط تغییر نتیجه توضیح داده شود و نباید به‌عنوان پیش‌بینی علمی پشیمانی ارائه شود.

### IV. Evidence-Grounded AI, Retrieval and Streaming

هر claim دربارهٔ محصول، variant، offer، review یا بازار MUST به source قابل ردیابی، زمان retrieval و سطح evidence
متصل یا صریحاً user-reported/unknown/assistant inference باشد. bounded retrieval MUST policy منبع، freshness، failure
و محدودیت پوشش را حفظ کند؛ unavailable source نباید با memory مدل جایگزین شود. streaming MUST فقط delta متن غیرقطعی
و progress واقعی عملیات را نمایش دهد؛ claim خام تا عبور از validation/publishing boundary fact یا recommendation نهایی
محسوب نمی‌شود و UI MUST بتواند provisional content را retract یا correct کند. hidden chain-of-thought نمایش داده
نمی‌شود. structured contract، timeout، cancellation، retry، validation، cost limit و evaluation case MUST پیش از
اتصال live مشخص شوند؛ fixture/mock MUST صریحاً غیرزنده نامیده شود.

### V. Privacy, Consent and Secret Safety

فقط داده لازم برای requirement مصوب MAY جمع‌آوری شود. هر داده persistشده MUST purpose، retention، deletion path،
access boundary و owner مشخص داشته باشد. preference memory فقط opt-in است؛ explicit و inferred-candidate preference،
self/gift/household context و temporary conversation MUST جدا باشند و کاربر MUST بتواند review، correct، delete و
disable کند. sensitive trait یا diagnosis از رفتار خرید استنباط نمی‌شود. user-owned API credential فقط backend-side،
encrypted at rest، masked در UI و قابل replace/delete است؛ secret، private conversation و داده حساس MUST NOT وارد
frontend bundle، URL، localStorage، log، analytics، prompt غیرضروری، screenshot، Git یا merchant request شود.

### VI. Accessible Persian and RTL Experience

تجربه کاربر MUST فارسی و RTL را به‌عنوان حالت اصلی پشتیبانی کند، نه patch نهایی. semantics، keyboard navigation،
focus، contrast، خوانایی عدد و متن دوزبانه، error message، responsive behavior و reduced motion MUST در acceptance
criteria و automated testهای مناسب پوشش داده شوند. streaming announcement باید خوانا، محدود و قابل توقف باشد.
accessibility regression یک defect محصول است.

### VII. Low-Cost Maintainable Deployment

معماری MUST در یک repository و modular monolith روی یک سرور کوچک قابل استقرار بماند، مگر measurement نیاز دیگری را
ثابت کند. crawling/retrieval MUST on-demand، محدود به pages/domains/time/bytes/concurrency و دارای cache/deduplication
و cancellation باشد. کوچک‌ترین transport مناسب streaming انتخاب می‌شود؛ WebSocket، queue یا worker جدا فقط با نیاز
concrete مجاز است. production configuration، health/readiness، proxy buffering/timeouts، migration، persistent storage،
backup/restore، graceful shutdown و rollback MUST پیش از deployment مشخص و تمرین شوند. هزینه provider، research و
عملیات MUST در تصمیم‌های معماری consequential لحاظ شود.

### VIII. Verification Before Completion

هیچ تغییر، test، build، migration، workflow، source integration یا live behavior نباید بدون command تازه و output
خوانده‌شده «موفق» یا «کامل» اعلام شود. behavior، permission، ownership، evidence boundary، cancellation و failure
caseهای meaningful MUST با test repeatable بررسی شوند؛ browser exploration، source-text matching، search snippet و
mock-only assertion جایگزین extraction یا آزمون رفتار واقعی نیستند. نتیجه‌های اجرا‌نشده، blocked، unavailable یا failed
MUST با همان وضعیت واقعی گزارش شوند.

## Product and Technical Constraints

- محصول MUST برای informed choice بهینه شود، نه افزایش خرید، فروش، affiliate conversion یا budget expansion.
- motivationهای enjoyment، celebration، self-reward و gift مشروع‌اند و MUST NOT impulsivity یا diagnosis تلقی شوند.
- warning فقط با mismatch توضیح‌پذیر budget، compatibility، size، intended use، ownership cost، conditions یا quality
  concern دارای support کافی مجاز است؛ preference tradeoff و insufficient information MUST جدا بمانند.
- پوشش interface چنددسته‌ای مجاز است، اما source coverage و recommendation readiness هر category MUST صریح باشد.
- research فقط bounded و on-demand است. authentication/CAPTCHA/paywall/anti-bot bypass، large-scale crawling، automatic
  checkout، purchasing و price notification خارج از scope هستند.
- product fact، current price، availability، review claim و merchant condition MUST از source مشخص یا input صریح
  کاربر بیاید؛ نبود source یا variant match MUST به‌عنوان unknown گزارش شود.
- React + TypeScript + Vite، Django + DRF، PostgreSQL، Docker Compose، same-origin و single-server modular monolith
  direction تاییدشده باقی می‌مانند. fixture development از real integration جدا است.
- runtime AI feature جدید direct OpenAI-only است؛ user-owned key مجوز eligibility، هزینه یا region support نیست و
  fallback پنهان به provider دیگر ممنوع است. ChatGPT subscription و API billing MUST جدا توضیح داده شوند.
- guest-first MAY باقی بماند، اما browser loss، نبود cross-device recovery، credential ownership و retention متفاوت
  conversation/preference/credential/research-cache/accounting MUST صریح باشند؛ account اجباری بدون تصمیم تازه مجاز نیست.

## Development Workflow and Quality Gates

- GitHub Spec Kit رسمی تنها مالک SDD است. هر feature MUST مسیر constitution، specification، clarification لازم، plan،
  tasks، analyze و implementation مجاز همان نسخه نصب‌شده را طی کند؛ workflow برنامه‌ریزی موازی ممنوع است.
- agent یا engineer MUST پیش از implementation، constitution، اسناد authoritative و feature spec مرتبط را بخواند و
  داخل phase مجاز بماند.
- هر دسته کار substantive MUST skill مرتبط داشته باشد. نصب skill جدید MUST از نظر overlap، dependency، license،
  maintenance، provenance، pin و phase timing ارزیابی و در `docs/tooling.md` ثبت شود.
- implementation behavior یا bugfix MUST با red/green/refactor انجام شود، مگر exception صریح و ثبت‌شده برای artifact
  تولیدشده، prototype دورریختنی یا تغییر صرفاً مستندی.
- source feasibility MUST میان documentation accessible، observed response و extraction موفق تمایز بگذارد و robots،
  terms/access policy، variant identity، freshness، rate limits، data quality، failure و cost را ثبت کند.
- review MUST defect-first، مبتنی بر diff و source و read-only باشد. finding باید concrete، قابل بازتولید و متناسب با
  severity باشد. analyze read-only است و remediation فقط در workflow مناسب انجام می‌شود.
- browser، frontend، backend، AI، retrieval و deployment tooling فقط در trigger فاز ثبت‌شده ارزیابی می‌شوند؛ popularity
  یا publisher name به‌تنهایی evidence انتخاب نیست.

## Governance

این constitution بر راهنماها و عادت‌های ناسازگار پروژه مقدم است؛ با این حال تصمیم محصول جدید را جعل یا اختیار کاربر
را گسترش نمی‌دهد. amendment نیازمند rationale، اثر بر specification/templateهای مصرف‌کننده، تصویب product lead و ثبت
تاریخ است.

نسخه‌بندی از semantic versioning پیروی می‌کند: حذف یا بازتعریف ناسازگار اصل MAJOR، افزودن اصل یا گسترش material آن
MINOR، و شفاف‌سازی غیرمعنایی PATCH است. هر plan و review MUST compliance با اصول مرتبط را بررسی کند. deviation فقط با
دلیل، scope، ریسک و مسیر بازگشت ثبت‌شده مجاز است. `AGENTS.md` قواعد اجرایی و `docs/decisions.md` وضعیت تصمیم‌های محصول
را نگه می‌دارند؛ هیچ‌کدام جای این constitution را نمی‌گیرند.

**Version**: 2.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-15
