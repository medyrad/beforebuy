# تحویل Phase 1 — Purchase Decision Analysis Specification

## وضعیت فاز

Phase 1 در مرز specification متوقف شد. feature specification نخستین تحلیل end-to-end برای **product review**
آماده است، اما برای plan، tasks یا implementation تصویب نشده است. هیچ application scaffold، frontend/backend
dependency، browser/AI integration یا deployment artifact ایجاد نشد.

## artifactهای ایجادشده

canonical feature directory:

- `specs/001-purchase-decision-analysis/spec.md` — specification اصلی با ۳۰ functional requirement.
- `specs/001-purchase-decision-analysis/scenarios.md` — ۱۱ scenario synthetic؛ نه user research.
- `specs/001-purchase-decision-analysis/questionnaire.md` — purchase context، هشت core question و سه
  follow-up شرطی.
- `specs/001-purchase-decision-analysis/decision-rubric.md` — rubric categorical پیشنهادی `PDA-CAT-v0.1`.
- `specs/001-purchase-decision-analysis/acceptance.md` — ۳۴ Given/When/Then acceptance criterion و mapping.
- `specs/001-purchase-decision-analysis/checklists/requirements.md` — checklist داخلی quality مربوط به
  `$speckit-specify` با ۲۲ item reviewed.
- `.specify/feature.json` — اشاره canonical به feature directory بالا.

اسناد project:

- `docs/decisions.md` — جهت supplied by product lead از assumption/user research جدا شد و open questionها
  به سه مورد کاهش یافت.
- `docs/product-brief.md` — evidence boundary، same-browser history، score deferral و AI failure proposal.
- `docs/tooling.md` — وضعیت واقعی discovery و failure مربوط به custom checklist/review-agent.
- `README.md` — وضعیت Phase 1 و navigation specification.
- `docs/archive/phase-0-handoff.md` — snapshot byte-for-byte از handoff قبلی پیش از جایگزینی.
- `docs/handoff.md` — همین handoff.

`test.txt` خالی حفظ شد. remote، push، commit و staging انجام نشد.

## workflowها و skillهای واقعاً استفاده‌شده

- `purchase-regret-project` در catalog بومی این session discover و برای تفکیک decision/proposal/assumption و
  حفظ phase boundary استفاده شد.
- `$speckit-specify` بومی discover شد. pre-hook وجود نداشت؛ `spec-template` با
  `resolve-template.sh spec-template --json` resolve شد؛ sequential feature path برابر
  `specs/001-purchase-decision-analysis` و `.specify/feature.json` ایجاد شد؛ post-hook نیز وجود نداشت.
- checklist داخلی `$speckit-specify` ساخته و پس از review iteration اول ۲۲/۲۲ item آن checked شد. این
  checkboxها فقط quality specification را نشان می‌دهند، نه implementation یا automated test.
- `$speckit-checklist` بومی discover و prerequisite رسمی آن اجرا شد، اما با خطای واقعی
  `plan.md not found ... Run $speckit-plan first` متوقف شد. چون Phase 1 ساخت plan را ممنوع کرده، plan جعلی
  و custom checklist تولید نشد. recovery: پس از ایجاد plan در فاز مجاز آینده، command دوباره اجرا شود.
- `review-agent` در catalog بومی این session وجود نداشت، هرچند فایل محلی قدیمی آن روی disk موجود بود؛ هیچ
  review-agent run ادعا نمی‌شود. review با checklist Spec Kit و inspection مستقیم انجام شد.
- `systematic-debugging` برای دو failure محیطی/command به‌کار رفت: نبود `jq` و false positive جست‌وجوی
  clarification marker. template JSON با parser استاندارد Python موجود خوانده شد و search scope اصلاح شد؛
  ابزار جدید نصب نشد.
- `$speckit-plan`, `$speckit-tasks`, `$speckit-implement`, `$speckit-analyze` و `$speckit-clarify` اجرا نشدند.

## جهت product ثبت‌شده

این موارد از product lead در prompt Phase 1 آمده‌اند و finding حاصل از research نیستند: mobile phones،
Persian/RTL، guest-first بدون account اجباری، same-browser history با delete/clear، نبود cross-device
recovery/public sharing، ورود دستی model/price، ۵–۸ core question و حداکثر سه follow-up، ممنوعیت numerical
score پیش از rubric review، mock فقط برای development/test و الزام real AI پیش از live-ready.

## questionnaire پیشنهادی

purchase context شامل target model، approximate price به تومان و current-device label اختیاری است. هشت سؤال
core عبارت‌اند از:

1. وضعیت دستگاه فعلی.
2. دلیل اصلی خرید.
3. مهم‌ترین مشکل یا محدودیت فعلی.
4. حداکثر سه intended use.
5. expected benefit اصلی.
6. urgency.
7. maximum stated budget به تومان.
8. alternative/tradeoffهای واقعاً قابل بررسی.

سه follow-up فقط برای contradiction، benefit/usage نامعلوم و evidence نامعلوم درباره capability ضروری هدف
هستند. income، debt، identity و contact پرسیده نمی‌شود. رقم فارسی/لاتین normalize می‌شود؛ zero، negative،
decimal، scientific notation و currency مبهم پیش از rubric رد می‌شوند.

## evidence boundary

هر evidence یکی از `USER_REPORTED`, `DETERMINISTICALLY_DERIVED`, `VERIFIED_EXTERNAL`, `UNKNOWN` است. در
first slice هیچ verified external product fact وجود ندارد. model name و price دستی camera، battery، workload
performance، software support، market value یا competitive price را ثابت نمی‌کند. user-reported capability
نیز verified نیست. missing evidence نه negative evidence است و نه score پایین.

report بدون technical comparison جعلی همچنان budget arithmetic، replacement need/benefit، usage clarity،
urgency، tradeoff و unknownهای actionable را توضیح می‌دهد. named alternative product مجاز نیست.

## rubric categorical پیشنهادی

چهار dimension مستقل‌اند: Budget fit، Replacement need/expected benefit، Evidence sufficiency و Unresolved
tradeoffs. validation نامعتبر execution را متوقف می‌کند. budget mismatch معلوم headline را می‌گیرد و unknown
ثانویه را پنهان نمی‌کند. در budget within، insufficiency/contradiction قبل از benefit outcome اعمال می‌شود.

headline outcomeها:

- `BUDGET_MISMATCH`
- `INSUFFICIENT_INFORMATION`
- `PURCHASE_REASONABLE`
- `DISCRETIONARY_PURCHASE_REASONABLE`
- `RECONSIDER_OR_WAIT`

Purchase Fit Score اصلی حذف نشده؛ numerical implementation آن deferred است. در این نسخه weight و threshold
عددی پیشنهاد نشده تا precision ساختگی ایجاد نشود.

### سه worked scenario

1. **دستگاه خراب، price = ۲۰ میلیون، budget = ۲۵ میلیون، essential benefit روشن** →
   `PURCHASE_REASONABLE`. report technical capability مدل هدف را تایید نمی‌کند.
2. **دستگاه سالم، خرید برای enjoyment، price درون budget و tradeoff پذیرفته‌شده** →
   `DISCRETIONARY_PURCHASE_REASONABLE`. enjoyment diagnosis یا automatic failure نیست.
3. **دستگاه خراب و urgent، price = ۳۰ میلیون، budget = ۱۸ میلیون** → `BUDGET_MISMATCH` همراه recognition
   نیاز فوری؛ نه diagnosis مالی و نه پیشنهاد تلفن نام‌دار.

scenario چهارم rubric نیز gaming با performance unknown را به `INSUFFICIENT_INFORMATION` می‌برد، نه score
فنی پایین.

## history، editing و failure proposal

- same-browser history یعنی دسترسی فقط تا وقتی guest ownership information همان browser موجود است؛ پاک‌شدن
  آن recovery ندارد و cross-device promise وجود ندارد.
- analysis ID به‌تنهایی proof مالکیت نیست. guest context باید proof دیگری داشته باشد، بدون اینکه این spec
  mechanism نهایی auth/session را تحمیل کند.
- کاربر یک report یا تمام history خود را حذف می‌کند؛ direct access نیز پس از حذف قطع می‌شود.
- proposal review: retention برابر ۹۰ روز از creation، non-sliding، با expiry قابل مشاهده است.
- proposal review: فقط input لازم، normalized money، answer set، report/evidence، rubric version/status و
  timestamps persist شوند؛ identity/contact، fingerprint و raw AI prompt/response ذخیره نشوند.
- analysisی که پیش از rubric کاملاً fail شود در history نیست؛ `RULE_BASED_LIMITED` result با label روشن
  می‌تواند در history باشد.
- هر edit موثر، deterministic result، evidence list و AI prose قبلی را stale می‌کند. reanalysis فقط از input
  جدید استفاده می‌کند.
- AI timeout/malformed response در صورت امکان یک report محدود rule-based با retry state می‌دهد؛ fabricated
  narrative یا prose قدیمی نشان داده نمی‌شود.

## scope changes نسبت به brief اصلی

- guest-first و same-browser history از open assumption به جهت first slice تبدیل شدند.
- delete individual/all اضافه و cross-device recovery/public sharing صریحاً خارج از first slice شدند.
- numerical score برای first slice deferred و rubric categorical برای review پیشنهاد شد؛ concept score حذف نشد.
- evidence boundary سخت‌تر شد: first slice هیچ technical comparison یا verified product fact ندارد.
- AI failure به limited deterministic result + retry state تبدیل شد.
- usefulness feedback از first slice deferred شد، اما از concept کلی MVP حذف نشد.
- retention ۹۰روزه و persistence fields proposal هستند و هنوز decision approved نیستند.

## checkهای واقعاً اجراشده

- canonical feature resolution در `.specify/feature.json` بررسی شد.
- countها: ۱۱ synthetic scenario، ۸ core question، ۳ follow-up، ۳۰ FR و ۳۴ AC.
- definition IDها برای `FR`, `SYN`, `Q`, `F`, `AC` unique بودند.
- local Markdown linkهای README و feature artifactها resolve شدند.
- evidence labels، insufficient-information outcome، discretionary outcome و retention proposal presence
  بررسی شدند.
- هیچ `[NEEDS CLARIFICATION: ...]` marker در authored requirements باقی نماند.
- هیچ React/Django/PostgreSQL/Docker یا architecture stack در feature artifactها وارد نشد.
- هیچ `plan.md`, `tasks.md` یا application dependency manifest ایجاد نشد.
- `test.txt` خالی و staged diff خالی ماند.
- این‌ها documentation/specification check هستند؛ automated behavior test، build یا implementation test اجرا نشد.

اولین consistency search خود checklist را به‌خاطر متن توضیحی marker match کرد؛ آن run pass محسوب نشد. search
اصلاح‌شده فقط authored requirements را بررسی کرد و marker واقعی پیدا نکرد.

## سه سؤال consequential باقیمانده

1. **آیا retention برابر ۹۰ روز از creation، بدون تمدید با بازدید، و persistence fields حداقلی پیشنهادی تایید
   می‌شوند؟**
   پیشنهاد: بله؛ مدت مشخص برای revisit می‌دهد و privacy/minimization را قابل آزمون نگه می‌دارد.

2. **آیا rubric categorical `PDA-CAT-v0.1` و deferred ماندن numerical Purchase Fit Score برای first slice
   تایید می‌شود؟**
   پیشنهاد: بله؛ رفتار قابل review و deterministic می‌ماند و precision بدون weight معتبر ایجاد نمی‌شود.

3. **آیا انتخاب provider/model و سقف request/token/cost به Phase AI integration موکول شود، با شرط اینکه قبل
   از live-ready تصویب و evaluation شود؟**
   پیشنهاد: بله؛ specification فعلی provider-neutral می‌ماند، ولی mock هرگز معیار live-ready نمی‌شود.

## handoff boundary

این specification **ready for product review** است، نه approved for implementation. گام بعدی product lead
review و پاسخ به سه سؤال بالاست. فقط پس از approval و prompt فاز بعد می‌توان `$speckit-plan` را اجرا کرد؛
frontend/backend/browser/AI tooling نیز فقط در trigger فاز مربوط ارزیابی می‌شود.
