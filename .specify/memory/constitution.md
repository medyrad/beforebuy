<!--
Sync Impact Report
- Version change: template (unratified) → 1.0.0
- Modified principles: placeholder principles → eight project-specific principles
- Added sections: Product and Technical Constraints; Development Workflow and Quality Gates
- Removed sections: none
- Follow-up TODOs: none
-->
# Purchase Regret Predictor Constitution

## Core Principles

### I. Lean Scope

هر feature MUST یک نیاز تاییدشده یا acceptance criterion مشخص را پاسخ دهد. MVP MUST به تلفن همراه و
جریان تصمیم‌یار مصوب محدود بماند. dependency، service، abstraction و infrastructure جدید فقط با نیاز
concrete، گزینه‌های بررسی‌شده و هزینه عملیاتی ثبت‌شده مجاز است. Redis، Celery، Kubernetes،
microservices، vector database و agent orchestration بدون نیاز مصوب ممنوع‌اند.

### II. Traceable Requirements and Acceptance Criteria

هر تغییر رفتاری MUST به feature specification و acceptance criteria قابل آزمون قابل ردیابی باشد.
تصمیم مصوب، proposed default، assumption و open question MUST جدا ثبت شوند و assumption نباید بدون
تصمیم صریح به requirement تبدیل شود. تغییر consequential MUST اسناد و specificationهای متاثر را در
همان change به‌روزرسانی کند.

### III. Explainable Deterministic Scoring

Purchase Fit Score، risk indicator، weight و threshold MUST از business ruleهای مشخص، deterministic،
نسخه‌پذیر و testable به دست آیند. LLM MUST NOT score authoritative را بسازد یا rule مفقود را حدس بزند.
هر نتیجه MUST بتواند input evidence، rule اجراشده و uncertainty یا داده مفقود را توضیح دهد. تا پیش از
تصویب ruleها، score production نباید پیاده‌سازی یا نمایش داده شود.

### IV. Evidence-Grounded AI and Explicit Uncertainty

AI فقط MAY متن را تفسیر کند، ابهام را شناسایی کند، پرسش روشن‌کننده بسازد و evidence موجود را توضیح
دهد. AI MUST NOT مشخصات محصول، قیمت جاری، وضعیت کاربر یا confidence ساختگی تولید کند. missing
information MUST از negative evidence جدا بماند. structured contract، timeout، failure behavior، cost
limit و evaluation case MUST پیش از اتصال provider زنده مشخص شوند؛ mock MUST صریحاً mock نامیده شود.

### V. Privacy and Minimal Collection

فقط داده لازم برای requirement مصوب MAY جمع‌آوری شود. هر داده persistشده MUST purpose، retention،
deletion path و access boundary مشخص داشته باشد. secret و داده حساس MUST وارد repository، log، prompt
غیرضروری یا artifact تست نشود. guest-first و account-based بودن تا زمان تصمیم محصول open باقی می‌ماند
و implementation نباید آن را پیش‌فرض پنهان کند.

### VI. Accessible Persian and RTL Experience

تجربه کاربر MUST فارسی و RTL را به‌عنوان حالت اصلی پشتیبانی کند، نه patch نهایی. semantics، keyboard
navigation، focus، contrast، خوانایی عدد و متن دوزبانه، error message و responsive behavior MUST در
acceptance criteria و automated testهای مناسب پوشش داده شوند. accessibility regression یک defect
محصول است.

### VII. Low-Cost Maintainable Deployment

معماری MUST برای یک repository و modular monolith قابل استقرار روی یک سرور کوچک طراحی شود، مگر اینکه
measurement نیاز دیگری را ثابت کند. production configuration، health check، migration، persistent
storage، backup/restore و rollback MUST پیش از deployment مشخص و تمرین شوند. هزینه provider و عملیات
MUST در تصمیم‌های معماری consequential لحاظ شود.

### VIII. Verification Before Completion

هیچ تغییر، test، build، migration یا workflow نباید بدون command تازه و output خوانده‌شده «موفق» یا
«کامل» اعلام شود. behavior و failure caseهای meaningful MUST با test repeatable بررسی شوند؛ browser
exploration، source-text matching و mock-only assertion جایگزین آزمون رفتار واقعی نیستند. نتیجه‌های
اجرا‌نشده، unavailable یا failed MUST با همان وضعیت واقعی گزارش شوند.

## Product and Technical Constraints

- محصول MUST برای informed decision بهینه شود، نه افزایش خرید، فروش یا affiliate conversion.
- محصول MUST NOT ادعای پیش‌بینی اعتبارسنجی‌شده پشیمانی آینده یا تشخیص روان‌شناختی داشته باشد.
- storefront، checkout، payment، retailer scraping، custom model training، native mobile و broad
  multi-category recommendation در MVP خارج از دامنه‌اند.
- جهت تاییدشده React، Django و Dockerized deployment است. React + TypeScript + Vite، Django REST
  Framework، PostgreSQL، Docker Compose و single-server deployment تا زمان تصویب، proposed default
  باقی می‌مانند.
- product fact و current price MUST از source مشخص یا input صریح کاربر بیاید؛ نبود source MUST به‌عنوان
  unknown گزارش شود.

## Development Workflow and Quality Gates

- GitHub Spec Kit رسمی تنها مالک SDD است. هر feature MUST مسیر specification، clarification لازم، plan،
  task و implementation همان نسخه نصب‌شده را طی کند؛ workflow برنامه‌ریزی موازی ممنوع است.
- agent یا engineer MUST پیش از implementation، constitution، اسناد authoritative و feature spec مرتبط
  را بخواند و داخل phase مجاز بماند.
- هر دسته کار substantive MUST skill مرتبط داشته باشد. نصب skill جدید MUST از نظر overlap، dependency،
  license، maintenance و phase timing ارزیابی و در `docs/tooling.md` ثبت شود.
- implementation behavior یا bugfix MUST با چرخه red/green/refactor انجام شود، مگر exception صریح و ثبت‌شده
  برای artifact تولیدشده، prototype دورریختنی یا تغییر صرفاً مستندی.
- review MUST defect-first، مبتنی بر diff و source، و read-only باشد. finding باید concrete، قابل بازتولید
  و متناسب با severity باشد.
- code-intelligence، browser، frontend، backend، AI و deployment tooling فقط در trigger فاز ثبت‌شده ارزیابی
  می‌شوند؛ popularity به‌تنهایی evidence انتخاب نیست.

## Governance

این constitution بر راهنماها و عادت‌های ناسازگار پروژه مقدم است؛ با این حال تصمیم محصول جدید را جعل یا
اختیار کاربر را گسترش نمی‌دهد. amendment نیازمند rationale، اثر بر specification/templateهای مصرف‌کننده،
تصویب product lead و ثبت تاریخ است.

نسخه‌بندی از semantic versioning پیروی می‌کند: حذف یا بازتعریف ناسازگار اصل MAJOR، افزودن اصل یا گسترش
material آن MINOR، و شفاف‌سازی غیرمعنایی PATCH است. هر plan و review MUST compliance با اصول مرتبط را
بررسی کند. deviation فقط با دلیل، scope، ریسک و مسیر بازگشت ثبت‌شده مجاز است. `AGENTS.md` قواعد اجرایی و
`docs/decisions.md` وضعیت تصمیم‌های محصول را نگه می‌دارند؛ هیچ‌کدام جای این constitution را نمی‌گیرند.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
