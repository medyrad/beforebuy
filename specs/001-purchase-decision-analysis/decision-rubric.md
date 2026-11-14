# Deterministic decision rubric

**Status**: `PDA-CAT-v0.3` implemented and verified in M1; M2 UI integration authorized, live AI remains deferred  
**Rubric ID**: `PDA-CAT-v0.3`  
**Output style**: categorical؛ بدون score، weight یا threshold عددی

## Purpose and invariant boundary

rubric چهار dimension مستقل را ارزیابی می‌کند: purchase justification، budget fit، target-model fit و
tradeoff state. سپس یک جدول ordered از همین statusها دقیقاً یک primary outcome انتخاب می‌کند. outcome مثبت فقط
وضعیت/انگیزه و stated budget را توصیف می‌کند؛ هرگز suitability فنی مدل هدف را ثابت نمی‌کند.

normalized inputs و rubric version یکسان همیشه dimension statusها، matched ruleها، primary outcome، unknownها
و actionها را یکسان می‌سازند. AI، prose، retry، rating و زمان اجرا حق تغییر آن‌ها را ندارند.

## Independent dimensions

| Dimension | Exactly-one status | Meaning |
|---|---|---|
| Budget fit | `WITHIN_BUDGET`, `ABOVE_BUDGET`, `BUDGET_UNKNOWN` | مقایسه deterministic price و stated budget؛ input نامعتبر پیش از rubric متوقف می‌شود |
| Purchase justification | `JUSTIFICATION_SUPPORTED`, `DISCRETIONARY_CLEAR`, `WEAK_OR_NONE`, `JUSTIFICATION_UNKNOWN`, `CONTRADICTORY` | آیا خرید/تعویض گوشی از وضعیت و benefit گزارش‌شده حمایت می‌گیرد؛ severity عددی یا «strong/moderate» ندارد |
| Target fit | `TARGET_FIT_UNVERIFIED`, `USER_REPORTED_SUPPORT`, `USER_REPORTED_MISMATCH` | در first slice state مثبت verified وجود ندارد؛ حتی support کاربر فقط user-reported است |
| Tradeoff state | `ACKNOWLEDGED`, `UNRESOLVED`, `NOT_REQUIRED` | فقط برای انتخاب discretionary gate است؛ alternativeهای صرفاً بررسی‌شده flag جدا هستند |
| Report mode | `AI_ASSISTED_SUCCESS`, `MOCK_ASSISTED`, `RULE_BASED_LIMITED` | metadata report و feedback است، نه ورودی outcome؛ mock هرگز live success نیست |

`REPAIR_NOTED` و `WAIT_NOTED` action flags هستند. انتخاب `REPAIR_CURRENT` یا `WAIT` در questionnaire فقط سبب
پیشنهاد «امکان/ترجیح را بررسی کنید» می‌شود و evidence feasibility، superiority یا sufficiency نیست.

## Validation and normalization

| Rule ID | Condition | Effect | Boundary |
|---|---|---|---|
| `VAL-01` | price صفر/منفی/decimal/scientific/malformed/currency مبهم | validation stop؛ report ایجاد نمی‌شود | price باید positive whole toman باشد |
| `VAL-02` | budget منفی/decimal/scientific/malformed/currency مبهم | validation stop؛ report ایجاد نمی‌شود | budget صفر و `UNKNOWN` معتبرند؛ missing به صفر تبدیل نمی‌شود |
| `BUD-01` | price معتبر و budget معلوم؛ `price <= budget` | `WITHIN_BUDGET` | فقط stated budget، نه income یا affordability کلی |
| `BUD-02` | price معتبر و budget معلوم؛ `price > budget`، شامل budget صفر | `ABOVE_BUDGET`; delta = `price - budget` | هیچ division، ratio یا درصد محاسبه نمی‌شود |
| `BUD-03` | budget = `UNKNOWN` | `BUDGET_UNKNOWN` | نه zero و نه within |

## Total justification evaluation

rules زیر به همین ترتیب اعمال می‌شوند؛ اولین match، status یگانه justification را می‌دهد. `F-001/F-002`
می‌توانند input را پیش از evaluation روشن کنند، اما اگر سقف follow-up تمام شود status scoped unknown/contradictory
باقی می‌ماند.

| Order / Rule | Current-device state | Expected benefit | Extra condition | Justification status |
|---|---|---|---|---|
| 1 / `JUS-01` | `WORKS_WELL` | `RESTORE_ESSENTIAL_ACCESS` یا `SOLVE_MAJOR_LIMIT` | contradiction پس از `F-001` حل نشده | `CONTRADICTORY` |
| 1 / `JUS-01` | `MINOR_PROBLEM` | `RESTORE_ESSENTIAL_ACCESS` یا `SOLVE_MAJOR_LIMIT` | contradiction پس از `F-001` حل نشده | `CONTRADICTORY` |
| 1 / `JUS-01` | `NO_DEVICE` | `SOLVE_MINOR_LIMIT` | contradiction پس از `F-001` حل نشده | `CONTRADICTORY` |
| 2 / `JUS-02` | `UNKNOWN` | هر value | follow-up نتوانسته state را روشن کند | `JUSTIFICATION_UNKNOWN` |
| 2 / `JUS-02` | هر state | `UNKNOWN` | follow-up نتوانسته benefit را روشن کند | `JUSTIFICATION_UNKNOWN` |
| 3 / `JUS-03` | هر state معلوم | `PERSONAL_ENJOYMENT` | motivation روشن است | `DISCRETIONARY_CLEAR` |
| 3 / `JUS-03` | `MINOR_PROBLEM` یا `WORKS_WELL` | `SOLVE_MINOR_LIMIT` | benefit روشن ولی replacement ضرورت‌محور نیست | `DISCRETIONARY_CLEAR` |
| 4 / `JUS-04` | `NO_DEVICE`, `UNUSABLE`, `SERIOUS_PROBLEM` | `RESTORE_ESSENTIAL_ACCESS`, `SOLVE_MAJOR_LIMIT` یا `ENABLE_IMPORTANT_NEW_USE` | برای `SERIOUS_PROBLEM` evidence روشن `F-001` در صورت trigger | `JUSTIFICATION_SUPPORTED` |
| 4 / `JUS-04` | `MINOR_PROBLEM` | `ENABLE_IMPORTANT_NEW_USE` | benefit user-reported روشن | `JUSTIFICATION_SUPPORTED` |
| 4 / `JUS-04` | `WORKS_WELL` | `ENABLE_IMPORTANT_NEW_USE` | new use مهم user-reported روشن | `JUSTIFICATION_SUPPORTED` |
| 5 / `JUS-05` | هر state معلوم | `NO_CLEAR_BENEFIT` | نبود benefit صریحاً توسط کاربر انتخاب شده | `WEAK_OR_NONE` |
| 6 / `JUS-06` | هر ترکیب معتبر باقی‌مانده | هر value باقی‌مانده | هیچ rule بالاتر match نشده | `JUSTIFICATION_UNKNOWN` |

`JUS-06` fallback totality است، نه تبدیل missing evidence به weakness. برای نمونه `SERIOUS_PROBLEM +
SOLVE_MINOR_LIMIT` تا وقتی رابطه مشکل و benefit روشن نشود unknown می‌ماند.

## Target-fit and tradeoff evaluation

| Rule ID | Condition | Effect | Required presentation/action |
|---|---|---|---|
| `FIT-01` | `F-003 = USER_REPORTS_IT_DOES_NOT_FIT` | `USER_REPORTED_MISMATCH` | concern prominent؛ action = reconsider/verify selected model |
| `FIT-02` | `F-003 = USER_REPORTS_IT_FITS` | `USER_REPORTED_SUPPORT` | صریحاً user-reported و independently unverified |
| `FIT-03` | `F-003 = NO_INFORMATION`، follow-up نمایش داده نشده، یا external verification وجود ندارد | `TARGET_FIT_UNVERIFIED` | unknown prominent؛ برای critical use action = verify capability |
| `TRD-01` | `Q-002` discretionary و `Q-006` شامل `ACCEPTED_TARGET_TRADEOFFS` | `ACKNOWLEDGED` | positive discretionary outcome مجاز می‌شود |
| `TRD-02` | `Q-002` discretionary و tradeoff accepted نیست/unknown است | `UNRESOLVED` | positive discretionary outcome ممنوع؛ scoped insufficient context |
| `TRD-03` | justification غیر-discretionary | `NOT_REQUIRED` | repair/wait flags فقط suggestion هستند |
| `ALT-01` | `Q-006` شامل `REPAIR_CURRENT` | `REPAIR_NOTED` | فقط «feasibility repair را بررسی کنید» |
| `ALT-02` | `Q-006` شامل `WAIT` | `WAIT_NOTED` | فقط «مزیت wait را بررسی کنید» |

## Single ordered primary-outcome selection

پس از محاسبه همه dimensionها، ردیف‌ها از بالا به پایین ارزیابی می‌شوند و اولین match دقیقاً یک primary outcome
می‌دهد. dimensionها و unknownها حتی وقتی headline دیگری مقدم است حفظ می‌شوند.

| Priority / Rule | Ordered condition | Primary outcome | Why / preserved information |
|---|---|---|---|
| 1 / `OUT-01` | Budget = `ABOVE_BUDGET` | `BUDGET_MISMATCH` | budget headline مقدم؛ justification، target fit، urgency و unknownها visible می‌مانند |
| 2 / `OUT-02` | Justification = `CONTRADICTORY` یا `JUSTIFICATION_UNKNOWN` | `INSUFFICIENT_CONTEXT` | contradiction/missing context قبل از positive justification؛ known budget و target fit حفظ می‌شوند |
| 3 / `OUT-03` | Target fit = `USER_REPORTED_MISMATCH` | `RECONSIDER_OR_WAIT` | evidence صریح کاربر علیه selected model؛ justification/budget ممکن است supported بماند |
| 4 / `OUT-04` | Justification = `WEAK_OR_NONE` | `RECONSIDER_OR_WAIT` | `NO_CLEAR_BENEFIT` evidence صریح است؛ صرف repair/wait-noted این outcome را فعال نمی‌کند |
| 5 / `OUT-05` | Justification = `DISCRETIONARY_CLEAR` و Tradeoff = `UNRESOLVED` | `INSUFFICIENT_CONTEXT` | enjoyment failure نیست؛ برای positive discretionary conclusion پذیرش tradeoff لازم است |
| 6 / `OUT-06` | Budget = `BUDGET_UNKNOWN` و Justification = `JUSTIFICATION_SUPPORTED` | `PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN` | justification supported؛ budget fit نامعلوم؛ target fit مستقل |
| 7 / `OUT-07` | Budget = `BUDGET_UNKNOWN` و Justification = `DISCRETIONARY_CLEAR` و Tradeoff = `ACKNOWLEDGED` | `DISCRETIONARY_CHOICE_BUDGET_UNKNOWN` | motivation/tradeoff روشن؛ budget fit نامعلوم |
| 8 / `OUT-08` | Budget = `WITHIN_BUDGET` و Justification = `JUSTIFICATION_SUPPORTED` | `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` | context و stated budget supported؛ selected model تأیید نمی‌شود |
| 9 / `OUT-09` | Budget = `WITHIN_BUDGET` و Justification = `DISCRETIONARY_CLEAR` و Tradeoff = `ACKNOWLEDGED` | `DISCRETIONARY_CHOICE_WITHIN_BUDGET` | انتخاب discretionary آگاهانه و در stated budget؛ selected model مستقل |
| 10 / `OUT-10` | هر ترکیب valid باقی‌مانده | `INSUFFICIENT_CONTEXT` | total fallback؛ هیچ valid combination بدون outcome نمی‌ماند |

## Compact decision coverage

| Boundary case | Dimension result | Primary outcome | Required unknown/action |
|---|---|---|---|
| Working device + important new use + budget within | justification supported؛ budget within | `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` | target fit unverified/support/mismatch جدا |
| Minor problem + clear minor benefit + tradeoffs acknowledged | discretionary clear؛ budget state مستقل | discretionary outcome متناسب با budget | target fit جدا؛ بدون necessity claim |
| Serious problem + unclear benefit | justification unknown | `INSUFFICIENT_CONTEXT` مگر above-budget که مقدم است | clarify benefit؛ known budget/fit visible |
| Enjoyment + unacknowledged/unknown tradeoffs | discretionary clear؛ tradeoff unresolved | `INSUFFICIENT_CONTEXT` مگر above-budget | ask/record bounded tradeoff clarification |
| No device + enjoyment + acknowledged tradeoffs | discretionary clear | discretionary outcome متناسب با budget | «no device» purchase necessity را به‌تنهایی ثابت نمی‌کند |
| Unknown current-device state | justification unknown | `INSUFFICIENT_CONTEXT` مگر above-budget | `F-001/F-002` یا scoped unknown |
| Unknown budget + weak justification | budget unknown؛ weak | `RECONSIDER_OR_WAIT` | budget unknown visible؛ no benefit evidence صریح |
| Unknown budget + contradictory justification | budget unknown؛ contradictory | `INSUFFICIENT_CONTEXT` | contradiction و budget unknown هر دو visible |
| User-reported target mismatch + otherwise supported | target mismatch | `RECONSIDER_OR_WAIT` مگر above-budget/justification blocker بالاتر | reconsider/verify selected model؛ need/budget preserved |
| Multiple matching rules | همه dimensionها محاسبه؛ outcome table ordered | اولین matched `OUT-*` فقط | matched rule list تمام matchها را برای explanation نگه می‌دارد |

## Boundary examples with actual Persian headlines

### A — supported phone purchase، budget fits، target unknown

- Outcome: `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET`.
- Headline: **«خرید یا تعویض گوشی با توجه به وضعیت فعلی قابل توجیه است و قیمت واردشده در محدوده بودجه
  شماست؛ مناسب‌بودن این مدل هنوز تأیید نشده است.»**

### B — repair merely noted must not override

- Inputs: justification supported، budget within، `REPAIR_NOTED`، feasibility unknown.
- Outcome: `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET`.
- Headline: **«خرید یا تعویض گوشی با وضعیت فعلی و بودجه شما سازگار است؛ امکان تعمیر فقط گزینه‌ای برای بررسی
  است و مناسب‌بودن مدل هدف هنوز تأیید نشده است.»**

### C — user-reported target mismatch

- Inputs: justification supported، budget within، target = `USER_REPORTED_MISMATCH`.
- Outcome: `RECONSIDER_OR_WAIT`.
- Headline: **«خرید یا تعویض گوشی از نظر وضعیت و بودجه قابل توجیه است؛ اما طبق اطلاعاتی که شما ارائه کردید،
  این مدل نیاز اصلی را پوشش نمی‌دهد، پس انتخاب مدل را بازبینی کنید.»**

### D — urgent replacement above budget

- Outcome: `BUDGET_MISMATCH`.
- Headline: **«خرید یا تعویض فوری گوشی با توجه به وضعیت فعلی قابل توجیه است؛ اما قیمت واردشده ۱۲٬۰۰۰٬۰۰۰
  تومان بالاتر از بودجه شماست و مناسب‌بودن این مدل نیز تأیید نشده است.»**

## Revision, retry and rating determinism

- edit answerها rubric ID/rule definition را تغییر نمی‌دهد؛ input revision تازه با همان rubric version از صفر
  recompute می‌شود. نتیجه قدیمی stale است.
- هر generation/retry به `input_revision_id` هدف bind می‌شود. response دیررس برای revision قدیمی، analysis
  deleted/expired یا rubric version دیگر publish نمی‌شود.
- report جاری یک `report_revision_id` و canonical report payload دارد. اگر retry report mode یا هر prose/
  evidence/outcome قابل‌مشاهده را عوض کند، report revision تازه ساخته و rating خالی می‌شود.
- اگر canonical payload و mode دقیقاً یکسان باشند، retry report را جایگزین نمی‌کند و rating جاری همان revision
  باقی می‌ماند. rating هرگز بی‌صدا به محتوای متفاوت یا mode دیگر منتقل نمی‌شود.

## AI output contract boundary

- هر claim باید علاوه بر evidence ID، با content/type همان evidence و ruleهای مجاز سازگار باشد؛ ID معتبر با
  claim بی‌ارتباط proof پشتیبانی نیست.
- output validator claimهای جدید، contradiction با dimension/outcome، product fact استنتاج‌شده از model name و
  instruction داخل user text را رد می‌کند.
- AI فقط structured interpretation candidate، bounded follow-up و explanation grounded می‌دهد. interpretation
  مؤثر بر deterministic result باید schema-valid و در موارد ambiguity برای کاربر قابل تأیید باشد.
- output rejected/timeout می‌تواند فقط `RULE_BASED_LIMITED` برای همان current revision بسازد؛ provider/model،
  timeout/retry limits و cost limits gate فاز integration هستند.

## Purchase Fit Score disposition

categorical rubric `PDA-CAT-v0.3` در M1 پیاده و پذیرفته شده است. Purchase Fit Score عددی حذف نشده، اما تا وجود
weight، threshold و validation قابل دفاع deferred است. Phase 4 فقط presentation و integration همین rubric را
مجاز می‌کند و مجوز M3/M4 نیست.
