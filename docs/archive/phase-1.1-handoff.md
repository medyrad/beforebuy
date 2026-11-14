# تحویل Phase 1.1 — اصلاحات بازبینی محصول

## وضعیت

feature موجود `specs/001-purchase-decision-analysis/` اصلاح شد؛ feature، plan، tasks، application code، dependency
یا future-phase tooling جدید ایجاد نشد. categorical outcomes و retention/feedback direction طبق تصمیم‌های
product lead ثبت شده‌اند، اما rubric دقیق `PDA-CAT-v0.2` هنوز final product review می‌خواهد.

**Ready for final product review; not yet approved for implementation.**

## تصمیم‌های ثبت‌شده و تغییرات

- retention pilot: ۹۰ روز از اولین persisted report (موفق یا limited)، non-sliding؛ visit، feedback، retry و
  edit reset نمی‌کنند؛ expiry فوراً access را می‌بندد و active purge target حداکثر ۲۴ ساعت است.
- categorical outcomes پذیرفته‌اند؛ numerical Purchase Fit Score حذف نشده و deferred است.
- AI provider/model/limits تا integration deferred؛ real provider + explicit limits + evaluation شرط live-ready.
- feedback اختیاری ۱ تا ۵ برگشته و به guest owner + analysis + current revision + report mode متعلق است.
- justification خرید/تعویض، budget fit و selected-model fit سه conclusion مستقل شده‌اند. نام outcomeهای مبهم
  قبلی حذف و scope outcomeهای مثبت محدود شد.
- price باید positive whole toman باشد؛ budget می‌تواند صفر، positive whole toman یا unknown باشد.
- persistence فقط latest required state است؛ logical revision ID وجود دارد، نه full revision history.
- AI claim بدون evidence/rule source، contradictory output و instruction داخل user text حق عبور ندارند.

## پرسش‌نامه نهایی و بار واقعی

Product entry:

1. `PC-001` — «چه تلفنی را برای خرید در نظر دارید؟»؛ متن ۲ تا ۱۲۰ نویسه.
2. `PC-002` — «قیمت تقریبی این خرید چند تومان است؟»؛ عدد صحیح مثبت تومان.

شش core question همیشه‌نمایان:

1. `Q-001` — «وضعیت گوشی فعلی شما کدام است؟»؛ no device/unusable/serious/minor/works well/unknown.
2. `Q-002` — «مهم‌ترین نتیجه‌ای که از این خرید انتظار دارید چیست؟»؛ restore essential، solve major، enable
   important new use، solve minor، enjoyment، no clear benefit یا unknown. reason و benefit اینجا ادغام شده‌اند.
3. `Q-003` — «این تلفن را بیشتر برای چه کارهایی می‌خواهید؟»؛ حداکثر سه use.
4. `Q-004` — «چه زمانی به این خرید نیاز دارید؟»؛ ۴۸ ساعت، دو هفته، سه ماه، flexible یا unknown.
5. `Q-005` — «حداکثر بودجه شما برای این خرید چند تومان است؟»؛ صفر، مبلغ صحیح مثبت یا unknown صریح.
6. `Q-006` — «کدام گزینه‌ها یا tradeoffها را واقعاً بررسی کرده‌اید؟»؛ repair/wait/keep/change requirements/
   accepted target tradeoffs/none/unknown.

pool مشترک follow-up، مجموعاً حداکثر سه سؤال:

1. `F-001` — مشکل اصلی/دلیل نبود گوشی برای رفع contradiction یا evidence مشکل serious.
2. `F-002` — clarification نتیجه مورد انتظار یا urgency ناشناخته.
3. `F-003` — evidence کاربر درباره suitability مدل برای استفاده critical؛ پاسخ مثبت نیز فقط user-reported است.

بار مسیر عادی دقیقاً **۸ interaction** (دو product + شش core) و طولانی‌ترین مسیر **۱۱ interaction** است. multi-select
یک interaction است و `OTHER` فیلد اضافه باز نمی‌کند. allowance جداگانه برای follow-up AI وجود ندارد.

## validation پول

- رقم فارسی/لاتین normalize می‌شود. comma لاتین، `٬` فارسی یا فاصله فقط با grouping سه‌رقمی معتبر پذیرفته‌اند.
- separator مخلوط، grouping بد، sign، decimal، `e/E`، scientific notation، حروف و currency غیرتومان silently
  اصلاح نمی‌شوند و پیام class-specific همراه نمونه تومان دارند.
- price صفر یا منفی invalid است. budget صفر valid و با هر price مثبت `ABOVE_BUDGET` است؛ delta = price و هیچ
  division/ratio انجام نمی‌شود. budget unknown هرگز صفر فرض نمی‌شود.

## جدول کامل rubric `PDA-CAT-v0.2`

| Rule | شرط | اثر / outcome | رفتار مرزی |
|---|---|---|---|
| `VAL-01` | price صفر/منفی/decimal/scientific/malformed/currency مبهم | validation stop؛ بدون report | correction تومان؛ بدون rounding |
| `VAL-02` | budget منفی یا syntax/currency نامعتبر | validation stop؛ بدون report | صفر یا unknown مجاز؛ missing به صفر تبدیل نمی‌شود |
| `BUD-01` | price مثبت و budget معلوم؛ `price <= budget` | `WITHIN_BUDGET` | فقط stated budget |
| `BUD-02` | `price > budget`، شامل budget صفر | `ABOVE_BUDGET`؛ delta = price-budget | بدون division/ratio |
| `BUD-03` | budget = `UNKNOWN` | `BUDGET_UNKNOWN` | نه zero و نه within |
| `NEED-01` | no device/unusable + essential/major benefit | `REPLACEMENT_STRONG` | target fit مستقل |
| `NEED-02` | serious problem + روشن‌بودن major/essential benefit | strong یا moderate | missing → `INFO-01` |
| `NEED-03` | works/minor + enjoyment/new use + tradeoff acknowledged | `DISCRETIONARY_CLEAR` | بدون diagnosis |
| `NEED-04` | works + no clear benefit | `WEAK_OR_NONE` | unknown هرگز weak نیست |
| `INFO-01` | context لازم بعد از follow-up unknown | `JUSTIFICATION_UNKNOWN` | known budget/fit باقی می‌ماند |
| `INFO-02` | contradiction consequential حل‌نشده | `CONTRADICTORY` | بدون averaging |
| `FIT-01` | capability externally verified نیست/no info | `TARGET_FIT_UNVERIFIED` | globally inconclusive نمی‌کند |
| `FIT-02` | user reports model fits | `USER_REPORTED_SUPPORT` | verified fact نیست |
| `FIT-03` | user reports model does not fit | `USER_REPORTED_CONCERN` | AI نمی‌تواند concern را حذف کند |
| `FIT-04` | critical use + unverified fit | unknown prominent + verify action | suitability claim ممنوع |
| `TRD-01` | repair considered + low urgency | `REPAIR_PLAUSIBLE` | feasibility فنی ادعا نمی‌شود |
| `TRD-02` | wait considered + flexible | `WAIT_PLAUSIBLE` | urgency unknown → unresolved |
| `TRD-03` | discretionary + accepted tradeoffs | `ACKNOWLEDGED` | unknown فنی باقی می‌ماند |
| `OUT-01` | budget above | `BUDGET_MISMATCH` | need/urgency/fit در summary |
| `OUT-02` | budget within + replacement strong/moderate | `REPLACEMENT_JUSTIFIED_WITHIN_BUDGET` | model fit مستقل |
| `OUT-03` | budget within + discretionary + acknowledged | `DISCRETIONARY_CHOICE_WITHIN_BUDGET` | model suitability تأیید نمی‌شود |
| `OUT-04` | weak benefit یا wait/repair plausible و فوریت پایین | `RECONSIDER_OR_WAIT` | unknown justification weak فرض نمی‌شود |
| `OUT-05` | justification unknown/contradictory و budget نه above | `INSUFFICIENT_CONTEXT` | فقط context نامعلوم را محدود می‌کند |
| `OUT-06` | budget unknown + justification supported | `REPLACEMENT_JUSTIFIED_BUDGET_UNKNOWN` یا `DISCRETIONARY_CHOICE_BUDGET_UNKNOWN` | budget within فرض نمی‌شود |

### precedence

1. `VAL-01/02` توقف کامل پیش از report.
2. dimensionهای budget، justification، target fit و tradeoff مستقل محاسبه می‌شوند.
3. `BUD-02` / `OUT-01` headline mismatch را می‌گیرد، ولی need/urgency/target fit پنهان نمی‌شوند.
4. `INFO-01/02` فقط conclusion justification را محدود می‌کنند؛ known dimensionها همچنان visible هستند.
5. `OUT-02/03/04/06` از justification + budget + tradeoff می‌آیند؛ target fit از outcome استنتاج نمی‌شود.
6. `FIT-03/04` باید headline یا summary مجاور و prominent باشند.
7. AI، feedback، visit، retry و edit rule/precedence را تغییر نمی‌دهند.

## چهار worked scenario با headline واقعی

1. **خرابی، replacement موجه، price در budget، target unknown**  
   `REPLACEMENT_JUSTIFIED_WITHIN_BUDGET` — «تعویض گوشی با توجه به وضعیت فعلی قابل توجیه است و قیمت
   واردشده در محدوده بودجه شماست؛ مناسب‌بودن این مدل هنوز تأیید نشده است.»  
   unknown: capability، reliability و market value مدل.

2. **خرید اختیاری affordable و tradeoff پذیرفته‌شده**  
   `DISCRETIONARY_CHOICE_WITHIN_BUDGET` — «این خرید یک انتخاب اختیاری است، در بودجه شما جا می‌گیرد و
   tradeoffهای اعلام‌شده را پذیرفته‌اید؛ مناسب‌بودن این مدل هنوز تأیید نشده است.»  
   unknown: suitability فنی و comparative value؛ enjoyment diagnosis نیست.

3. **gaming critical و performance هدف unknown**  
   `REPLACEMENT_JUSTIFIED_WITHIN_BUDGET` همراه `TARGET_FIT_UNVERIFIED` —
   «نیاز شما به تعویض و تناسب قیمت با بودجه قابل ارزیابی است؛ عملکرد این مدل برای بازی هنوز تأیید نشده،
   پس انتخاب همین مدل به بررسی معتبر نیاز دارد.»  
   unknown: gaming performance؛ این unknown known conclusionهای replacement/budget را حذف نمی‌کند.

4. **replacement فوری بالاتر از budget**  
   `BUDGET_MISMATCH` — «تعویض فوری گوشی با توجه به خرابی فعلی قابل توجیه است؛ اما قیمت واردشده
   ۱۲٬۰۰۰٬۰۰۰ تومان بالاتر از بودجه شماست و مناسب‌بودن این مدل نیز تأیید نشده است.»  
   unknown: target fit و گزینه جایگزین؛ نه hardship و نه مدل ارزان نام‌دار ادعا می‌شود.

## feedback، revision و metric

- prompt دقیق: «این تحلیل چقدر به تصمیم شما کمک کرد؟»؛ optional integer 1..5.
- یک rating جاری برای guest owner + analysis + current report revision؛ change/remove مجاز.
- edit، report قبلی را stale و revision جدید را بدون rating آغاز می‌کند. rating قدیمی attach نمی‌شود و چون فقط
  latest state persist می‌شود، از current metric خارج است.
- delete analysis، rating آن را نیز حذف می‌کند. `AI_ASSISTED_SUCCESS` و `RULE_BASED_LIMITED` متمایزند.
- تنها metric: average ratingهای submitted/currently retained + response count + breakdown بر اساس mode.
  این metric کاهش regret یا causal purchase outcome را اندازه نمی‌گیرد. dashboard/analytics SDK وجود ندارد.

## retention، deletion و persistence

- creation = اولین persisted report، شامل clearly-labeled limited report. failure بدون report persist نمی‌شود.
- expiry = creation + 90 days. visits، feedback، retries و edits همان analysis reset نمی‌کنند؛ analysis جدید
  lifecycle مستقل دارد.
- expired/deleted item فوراً از history/direct access unavailable؛ expired active record تا ۲۴ ساعت purge.
- erasure فوری backup ادعا نمی‌شود؛ backup lifecycle باید در deployment phase پیش از production readiness تعیین شود.
- فقط latest required answers/report/evidence/rubric/current revision/rating/mode/timestamps persist می‌شوند؛ full
  revision history، identity/contact/fingerprint و raw provider prompt/response ذخیره نمی‌شوند.
- delete هنگام in-flight generation/retry publication را invalid می‌کند؛ late result/rating discard و resurrection
  ممنوع است.

## AI boundary

هر claim باید به answer/evidence/rule وصل باشد. AI outcome یا deterministic facts را override نمی‌کند، از نام
مدل fact نمی‌سازد و unknown را suitability مثبت نمی‌کند. contradictory/unsupported output rejected است و فقط
limited deterministic result یا failure نمایش می‌یابد. متن کاربر data است، نه instruction.

## verification واقعی این correction

- همه artifactهای خواسته‌شده و docs affected به‌صورت source review شدند.
- consistency script تازه برای unique/resolved IDها، mapping FR، question/rule references، follow-up cap، headline
  overclaim، zero/unknown budget، feedback/lifecycle و absence plan/tasks/dependencies اجرا شد؛ نتیجه command و count
  نهایی در پاسخ تحویل گزارش می‌شود.
- Markdown linkها، feature pointer، نبود clarification marker و phase boundary بررسی شدند.
- این‌ها specification checks هستند؛ automated application test/build/browser test اجرا نشد چون application وجود ندارد.

## تعارض substantive باقی‌مانده

اصل categorical بودن تصمیم شده است، اما ruleها، precedence، identifierها و wording دقیق `PDA-CAT-v0.2` هنوز
باید product lead تأیید کند. backup lifecycle یک dependency deployment است و provider/model/limits یک تصمیم
AI-integration؛ هیچ‌کدام blocker بازبینی specification فعلی نیستند و نباید اکنون حدس زده شوند.

## مرز handoff

handoff پیشین در `docs/archive/phase-1-handoff.md` آرشیو شده است. گام بعد فقط final product review است؛
`$speckit-plan`, `$speckit-tasks`, `$speckit-implement` و tooling فازهای آینده اجرا نشده‌اند.

**Ready for final product review; not yet approved for implementation.**
