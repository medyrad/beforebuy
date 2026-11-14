# تحویل Phase 0

## وضعیت فاز

Phase 0 در مرز تعیین‌شده متوقف شد. workflow توسعه، اسناد lean محصول، constitution و مهارت‌های همین فاز
آماده‌اند. application scaffold، dependencyهای React/Django، business logic، database، service،
deployment و ابزارهای فازهای آینده ایجاد یا نصب نشده‌اند.

## تغییرات تکمیل‌شده

- repository محلی Git با شاخه `main` ایجاد شد؛ remote، commit و staging ساخته نشد.
- `test.txt` بدون تغییر و خالی حفظ شد.
- GitHub Spec Kit رسمی به‌صورت project-scoped با نسخه pin‌شده `v1.4.0` نصب شد و Codex integration در
  `.specify/` و `.agents/skills/speckit-*` مقداردهی شد.
- skillهای واقعی Spec Kit و نام فراخوانی `$speckit-*` از فایل‌های نصب‌شده کشف شدند.
- دستورالعمل کامل `$speckit-constitution` مستقیماً از skill نصب‌شده خوانده و workflow آن اجرا شد:
  template resolver موفق بود، hook قبل/بعد وجود نداشت و constitution نسخه `1.0.0` فقط در مسیر canonical
  `.specify/memory/constitution.md` نوشته شد. workflowهای specify/plan/tasks/implement اجرا نشدند.
- از Superpowers فقط `systematic-debugging`، `verification-before-completion` و
  `test-driven-development` نصب شدند. مهارت‌های planning/execution آن نصب نشدند تا با Spec Kit رقابت نکنند.
- برای code review از `review-agent` موجود و read-only استفاده خواهد شد؛ `requesting-code-review` به‌علت
  overlap و وابستگی به subagent نصب نشد.
- `grill-me` همراه dependency واقعی آن، `grilling`، نصب شد. wrapper با یک patch کوچک Codex-compatible شد
  و explicit-only باقی ماند.
- skill پروژه‌محور `purchase-regret-project` ایجاد شد و به اسناد authoritative ارجاع می‌دهد.
- licenseهای MIT مربوط به Spec Kit، Superpowers و Matt Pocock skills در `third_party/licenses/` حفظ شدند.
- trigger و روش ارزیابی frontend، backend، browser، AI، deployment و code-intelligence در
  `docs/tooling.md` ثبت شد؛ هیچ‌کدام در Phase 0 نصب نشدند.

## فایل‌های ایجاد یا تغییرکرده

- اسناد root: `.gitignore`, `README.md`, `AGENTS.md`.
- اسناد محصول: `docs/product-brief.md`, `docs/decisions.md`, `docs/tooling.md`, `docs/handoff.md`.
- Spec Kit managed files: `.specify/` و `.agents/skills/speckit-*`.
- skillهای Phase 0: `.agents/skills/systematic-debugging`,
  `.agents/skills/verification-before-completion`, `.agents/skills/test-driven-development`,
  `.agents/skills/grill-me`, `.agents/skills/grilling`, `.agents/skills/purchase-regret-project`.
- noticeها: `third_party/licenses/spec-kit-MIT.txt`, `third_party/licenses/superpowers-MIT.txt`,
  `third_party/licenses/mattpocock-skills-MIT.txt`.

## نسخه‌ها و sourceهای pin‌شده

- Spec Kit: `v1.4.0`, commit `14ddec8cb22db2a3b50e5ae6861b31053f132bfa`; workflow bundled
  `speckit 1.0.1`.
- Superpowers skills: commit `22f0b463e7a5e579904dd6211a520321035526f7`.
- Matt Pocock skills: repository version `1.3.2`, commit
  `5863806dd4e15c63174bee4e7515a4256792ecfa`، به‌اضافه patch سازگاری محلی ثبت‌شده در tooling inventory.
- project skill: revision اولیه repository-local در Phase 0.

## بررسی‌های واقعی و نتیجه

- `.tools/bin/specify --version` → `specify 1.4.0`.
- `.tools/bin/specify integration status` → `OK`، integration پیش‌فرض `codex`، مقدار
  `Modified managed files: 0`، `Missing managed files: 0` و `Invalid manifest paths: 0`.
- `.tools/bin/specify check` → Codex CLI را available و CLI را ready گزارش کرد.
- `.tools/bin/specify workflow list` → workflow bundled با نام `Full SDD Cycle (speckit) v1.0.1`.
- `resolve-template.sh constitution-template --json` → موفق؛ constitution از template فعال resolve شد.
- validator رسمی skill-creator با `PyYAML` موقت برای شش skill custom/third-party → همگی valid پس از patch
  سازگاری `grill-me`.
- validator عمومی skill-creator روی skillهای official Spec Kit کلید رسمی `compatibility` را نمی‌شناسد؛
  بنابراین برای آن‌ها pass ادعا نمی‌شود. صحت فایل‌های managed با `specify integration status` بررسی شد.
- reference pathهای skill پروژه، debugging، testing و dependency مربوط به grill → همگی موجود.
- لینک‌های نسبی README → همگی resolve شدند.
- placeholderهای constitution، تاریخ/version و هشت اصل → بررسی شدند؛ placeholder توضیح‌نداده باقی نماند.
- فهرست `.agents/skills` → هیچ skill مربوط به frontend، backend، Playwright یا code-intelligence نصب نشده است.
- جست‌وجوی assignmentهای credential-like خارج از `.git/` و `.tools/` → موردی پیدا نشد.
- `git diff --cached --name-only` → خالی؛ هیچ فایل staged نیست.
- `test ! -s test.txt` → موفق؛ فایل خالی باقی مانده است.

اولین اجرای validator به‌علت نبود module محلی `yaml` متوقف شد و pass محسوب نشد. اجرای معتبر بعدی با
`uv run --with PyYAML` و بدون افزودن dependency پروژه انجام شد.

## مانعها و دستور ادامه

فایل‌های skill در disk نصب‌اند، اما catalog مهارت‌های Codex در میانه همین turn دوباره load نمی‌شود؛ در نتیجه
discoverability native این skillهای تازه در این session قابل اثبات نبود. برای ادامه:

1. یک session/turn تازه Codex را از `/Users/mehdi/Projex/beforebuy` شروع کنید.
2. بررسی کنید `$speckit-constitution`, `$speckit-specify` و `$purchase-regret-project` در discovery دیده
   می‌شوند. اگر دیده نشدند، Codex/IDE را یک‌بار restart کنید و همین مسیر پروژه را دوباره باز کنید.
3. پس از پاسخ product lead و صدور prompt فاز بعد، feature را با `$speckit-specify` شروع کنید؛ در Phase 0
   هیچ plan، task یا implementation دیگری اجرا نشود.

مانع فنی دیگری برای تحویل Phase 0 مشاهده نشد. repository هنوز initial commit ندارد و همه فایل‌های Phase 0
طبق انتظار untracked هستند؛ commit کردن به product lead واگذار شده است.

## پرسش‌های consequential برای product lead

این پنج سؤال با روش design-tree مهارت `grilling` انتخاب شده‌اند؛ پاسخ «بله» در هر مورد پیشنهاد را می‌پذیرد.

1. **آیا MVP را guest-first و بدون account اجباری بسازیم و history را تا تصویب retention/deletion فقط با
   شناسه ناشناس و کنترل حذف کاربر طراحی کنیم؟**  
   پیشنهاد: بله؛ friction و جمع‌آوری داده شخصی را کم می‌کند، اما contract دقیق persistence باید پیش از
   implementation تصویب شود.

2. **آیا تا زمان تصویب ابعاد، ruleها و uncertainty، نمایش Purchase Fit Score را implementation نکنیم و
   Phase بعد را با تعریف مثال‌ها و acceptance criteria شروع کنیم؟**  
   پیشنهاد: بله؛ این کار مانع weight و threshold ساختگی و score تولیدشده توسط LLM می‌شود.

3. **آیا source داده MVP را فقط ورودی دستی کاربر نگه داریم و enrichment مشخصات/قیمت جاری را به تصمیم بعدی
   موکول کنیم؟**  
   پیشنهاد: بله؛ ریسک داده نادرست، scraping و هزینه عملیاتی را کاهش می‌دهد و با brief فعلی سازگار است.

4. **آیا questionnaire اولیه را در Phase بعد از چند سناریوی واقعی و business ruleهای scoring استخراج کنیم،
   به‌جای تثبیت فوری یک فهرست بلند field؟**  
   پیشنهاد: بله؛ سؤال‌ها باید evidence لازم برای ruleهای مشخص را جمع کنند و burden غیرضروری ایجاد نکنند.

5. **آیا نخست یک contract مستقل از provider و adapter mock با برچسب واضح بسازیم و انتخاب AI provider/model
   را تا تعیین سقف هزینه هر analysis عقب بیندازیم؟**  
   پیشنهاد: بله؛ قابلیت تست را حفظ و mock را از رفتار live جدا می‌کند، بدون lock-in زودهنگام.

## پیشنهاد فاز بعد

پس از پاسخ product lead، Phase 1 با `$speckit-specify` برای یک vertical slice کوچک آغاز شود. پیش از
implementation باید scoring، access/persistence و contract داده به requirement و acceptance criteria
صریح تبدیل شوند. انتخاب frontend/backend/browser/AI tooling فقط در trigger ثبت‌شده همان کار انجام شود.
