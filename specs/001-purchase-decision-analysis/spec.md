# Feature Specification: تحلیل تصمیم خرید تلفن همراه

**Feature Branch**: `main` (feature جدید یا branch جدید ایجاد نشد)  
**Created**: 2026-11-14  
**Last corrected**: 2026-11-14 — Phase 5 M3 live-explanation authorization and safety/cost closure  
**Status**: M1/M2 accepted; M3 adapter and evaluation harness are authorized. M4 remains deferred.  
**Supporting artifacts**: [Scenarios](scenarios.md) · [Questionnaire](questionnaire.md) ·
[Decision rubric](decision-rubric.md) · [Written acceptance](acceptance.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - گزارش scope‌شده و مبتنی بر شواهد (Priority: P1)

کاربر مهمان نام گوشی هدف و price را با واحد تومان وارد و شش سؤال کوتاه را پاسخ می‌دهد. report جداگانه
می‌گوید آیا خرید/تعویض با وضعیت کاربر توجیه دارد، آیا price در budget است، و آیا تناسب مدل هدف معلوم یا
نامعلوم است. تأیید دو مورد اول نباید سومی را تأیید جلوه دهد.

**Independent Test**: scenarioهای synthetic می‌توانند headline، dimensionها، evidence source، unknownها،
validation و outcome deterministic را از طریق API و رابط واقعی بررسی کنند.

**Acceptance Scenarios**:

1. **Given** گوشی فعلی خراب، target در budget و capability نامعلوم است، **When** report ساخته می‌شود،
   **Then** phone purchase justification و budget fit supported اعلام می‌شوند و «مناسب‌بودن این مدل هنوز تأیید نشده است» در headline
   یا summary بلافاصله مجاور دیده می‌شود.
2. **Given** خرید اختیاری در budget و tradeoffها پذیرفته شده‌اند، **When** report ساخته می‌شود، **Then**
   انتخاب discretionary آگاهانه توصیف می‌شود، بدون diagnosis یا تأیید suitability مدل.
3. **Given** gaming یک نیاز critical و performance هدف unknown است، **When** report ساخته می‌شود، **Then**
   unknown مدل برجسته می‌ماند ولی known conclusionهای replacement و budget حذف نمی‌شوند.
4. **Given** replacement فوری و price بالاتر از budget است، **When** rubric اجرا می‌شود، **Then** headline
   mismatch را همراه recognition نیاز فوری نشان می‌دهد.

---

### User Story 2 - اصلاح، revision و feedback اختیاری (Priority: P2)

کاربر می‌تواند input را اصلاح و analysis را دوباره تولید کند. هر report جاری یک logical revision ID دارد.
پس از report از کاربر پرسیده می‌شود «این تحلیل چقدر به تصمیم شما کمک کرد؟» و پاسخ اختیاری ۱ تا ۵ را می‌تواند
ثبت، تغییر یا حذف کند.

**Independent Test**: edit، stale state، revision جدید، عدم انتقال rating قدیمی و تفکیک mode گزارش قابل
بررسی است.

**Acceptance Scenarios**:

1. **Given** revision دارای rating است، **When** input مؤثر edit و report جدید تولید می‌شود، **Then** revision
   جدید rating ندارد و rating قبلی به آن متصل نمی‌شود.
2. **Given** deterministic report موجود و AI fail است، **When** limited revision نشان داده می‌شود، **Then**
   rating آن با mode `RULE_BASED_LIMITED` یا `MOCK_ASSISTED` ثبت و از `AI_ASSISTED_SUCCESS` متمایز می‌شود.

---

### User Story 3 - history خصوصی با lifecycle ثابت (Priority: P3)

کاربر مهمان در همان browser reportهای خود را باز، یکی یا همه را حذف می‌کند. lifecycle هر analysis با اولین
report persistشده، شامل limited report، آغاز و ۹۰ روز بعد بدون تمدید تمام می‌شود.

**Independent Test**: guest isolation، expiry، purge target، delete در retry in-flight و direct access قابل
بررسی است.

**Acceptance Scenarios**:

1. **Given** analysis به expiry رسیده، **When** history یا direct access درخواست می‌شود، **Then** فوراً
   unavailable است و active storage حداکثر تا ۲۴ ساعت بعد purge می‌شود.
2. **Given** generation/retry در جریان است، **When** analysis حذف می‌شود، **Then** نتیجه دیررس discard می‌شود
   و analysis را resurrect نمی‌کند.
3. **Given** guest دیگری فقط analysis ID را می‌داند، **When** direct access می‌خواهد، **Then** دسترسی ندارد.

### Edge Cases

- price صفر/منفی/اعشاری/scientific/malformed یا currency مبهم؛ budget صفر، unknown یا invalid.
- رقم فارسی/لاتین و grouping مجاز/نامعتبر.
- target model نام دارد ولی capability critical نامعلوم است.
- follow-up pool سه‌تایی تمام شده ولی context consequential unresolved است.
- AI timeout، malformed، unsupported یا contradictory output؛ prompt-like user text.
- feedback بعد از edit، remove rating، و تفاوت report mode.
- expiry هم‌زمان با صفحه باز؛ delete هم‌زمان با in-flight retry؛ late result.
- پاک‌شدن browser ownership information و نبود recovery.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: feature MUST فقط تصمیم خرید گوشی را در interface فارسی، RTL و دسترس‌پذیر پوشش دهد.
- **FR-002**: کاربر MUST بدون account اجباری analysis را کامل کند.
- **FR-003**: product entry MUST فقط target description و price دستی با label صریح تومان داشته باشد؛ نام
  دستگاه فعلی optional field جداگانه نیست.
- **FR-004**: price MUST عدد صحیح مثبت تومان باشد؛ price صفر، منفی، decimal، scientific notation، malformed
  یا currency مبهم MUST با پیام actionable رد شود.
- **FR-005**: budget MUST یکی از صفر تومان، عدد صحیح مثبت تومان یا `UNKNOWN` صریح باشد؛ منفی و syntax نامعتبر
  رد و missing/unknown MUST NOT به صفر تبدیل شود.
- **FR-006**: رقم فارسی/لاتین و grouping سه‌رقمی پشتیبانی‌شده MUST deterministic normalize شوند؛ budget صفر
  با هر price مثبت MUST بدون division error برابر `ABOVE_BUDGET` باشد.
- **FR-007**: journey MUST هشت primary input field داشته باشد: دو product field + دقیقاً شش core question؛
  longest path MUST حداکثر یازده question/input prompt باشد. این count تعداد user action نیست.
- **FR-008**: یک pool مشترک حداکثر سه conditional follow-up در کل flow MUST اعمال شود؛ AI و deterministic
  allowance جدا ندارند.
- **FR-009**: سؤال‌ها MUST فقط status، expected benefit، intended use، urgency، budget و tradeoff را جمع کنند
  و MUST NOT income، debt، identity یا contact بخواهند.
- **FR-010**: هر evidence item MUST یکی از `USER_REPORTED`, `DETERMINISTICALLY_DERIVED`,
  `VERIFIED_EXTERNAL`, `UNKNOWN` و source answer/rule مشخص داشته باشد.
- **FR-011**: در first slice هیچ product fact برابر `VERIFIED_EXTERNAL` نیست؛ model name یا AI memory MUST NOT
  capability، market value یا competitive price را ثابت کند.
- **FR-012**: report MUST justification خرید/تعویض، budget fit و target-model fit را سه conclusion مستقل نشان
  دهد؛ حمایت از دو مورد اول MUST NOT تأیید سومی تلقی شود.
- **FR-013**: unknown target fit MUST در headline یا summary بلافاصله مجاور visible باشد و MUST NOT همه analysis
  دستی را globally inconclusive کند.
- **FR-014**: missing evidence MUST `UNKNOWN` بماند، نه evidence منفی، low score یا positive suitability.
- **FR-015**: rubric deterministic و نسخه‌دار `PDA-CAT-v0.3` MUST مالک dimensionها، outcome و precedence باشد؛
  numerical Purchase Fit Score همچنان deferred است، نه حذف‌شده.
- **FR-016**: outcomeهای scoped MUST شامل `BUDGET_MISMATCH`, `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET`,
  `DISCRETIONARY_CHOICE_WITHIN_BUDGET`, `RECONSIDER_OR_WAIT`, `INSUFFICIENT_CONTEXT`,
  `PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN` و `DISCRETIONARY_CHOICE_BUDGET_UNKNOWN` باشند.
- **FR-017**: همه inputهای valid MUST dimension status صریح و دقیقاً یک primary outcome از جدول ordered داشته
  باشند؛ budget mismatch مقدم است، contradiction/unknown justification قبل از positive outcome می‌آید و
  target mismatch/weak benefit evidence لازم برای reconsider را فراهم می‌کنند.
- **FR-018**: discretionary purchase درون budget با tradeoff پذیرفته‌شده MAY supported باشد؛ enjoyment MUST
  NOT impulsivity، diagnosis یا failure تلقی شود.
- **FR-019**: report MUST supporting reasons، concerns، unknowns، attribution و actionهای عمومی buy/reconsider/
  wait/repair/verify را نشان دهد؛ صرفاً noted بودن repair/wait MUST NOT positive justification را override کند
  و report MUST NOT مدل جایگزین نام‌دار پیشنهاد دهد.
- **FR-020**: هر claim AI MUST به supplied evidence یا deterministic rule پیوند داشته باشد؛ AI MUST NOT rule،
  arithmetic، attribution، dimension، precedence یا outcome را override کند.
- **FR-021**: AI MUST NOT از model name product fact بسازد؛ user text MUST data تلقی شود و instruction درون آن
  MUST NOT reporting rule را تغییر دهد.
- **FR-022**: AI output متناقض یا unsupported MUST رد شود و successful report محسوب نشود؛ در صورت وجود result
  deterministic، `RULE_BASED_LIMITED` با retry state وگرنه failure بدون report رخ دهد.
- **FR-023**: mock فقط development/test است؛ live readiness نیازمند provider واقعی، limits صریح و evaluation
  است. mock output MUST mode `MOCK_ASSISTED` داشته باشد و با `AI_ASSISTED_SUCCESS` یا metric live-AI مخلوط نشود.
  M3 MUST مدل/prompt/schema صریح، input/output bound، timeout، retry گذرا و محدود، per-guest limit، budget/circuit
  breaker سراسری و evaluation spending cap مستقل داشته باشد. credential به‌تنهایی مجوز هزینه نیست.
- **FR-024**: history MUST فقط با guest ownership context همان browser در دسترس باشد؛ analysis ID به‌تنهایی
  proof مالکیت نیست و cross-device recovery/public sharing وجود ندارد. همه unsafe browser API operationها MUST
  برای anonymous guest با CSRF استاندارد Django مستقل از DRF authentication محافظت شوند.
- **FR-025**: کاربر MUST یک analysis یا تمام history خود را حذف کند؛ deleted/expired analysis از history و
  direct access unavailable است.
- **FR-026**: creation timestamp MUST زمان اولین report persistشده باشد، شامل `RULE_BASED_LIMITED`؛ failure
  بدون report analysis persistشده ایجاد نمی‌کند.
- **FR-027**: expiry MUST دقیقاً ۹۰ روز پس از creation و non-sliding باشد؛ visit، feedback، retry و edit همان
  analysis MUST آن را reset نکنند؛ analysis عمداً جدید lifecycle مستقل دارد. persist analysis جدید MUST guest
  session/access lifetime را حداقل تا expiry همان analysis تمدید کند؛ browser cookie loss/early expiry ممکن است
  دسترسی را زودتر قطع کند و recovery وعده داده نمی‌شود.
- **FR-028**: expired analysis MUST در لحظه expiry غیرقابل دسترسی شود و active-storage purge MUST حداکثر طی
  ۲۴ ساعت انجام شود؛ erasure فوری backup ادعا نمی‌شود و backup lifecycle پیش از production readiness لازم است.
- **FR-029**: first slice MUST فقط latest required answer/report state را persist کند؛ full revision history
  ذخیره نمی‌شود، اما هر report جاری MUST logical `report_revision_id` داشته باشد.
- **FR-030**: edit مؤثر MUST report جاری را stale و input revision تازه را با همان rubric version از input جدید
  recompute کند؛ prose/evidence قدیمی MUST reuse نشود.
- **FR-031**: generation/retry MUST به input revision و rubric version هدف bind باشد؛ response دیررس برای
  revision قدیمی یا analysis deleted/expired MUST discard شود و analysis/rating/history را overwrite یا resurrect نکند.
  clear-history MUST با guest generation epoch و transaction serialized، initial create قدیمی را invalid کند؛ competing
  retries روی همان input revision MUST operation token داشته باشند تا فقط تازه‌ترین operation publish کند.
- **FR-032**: پس از هر report جاری MUST سؤال «این تحلیل چقدر به تصمیم شما کمک کرد؟» با rating اختیاری ۱ تا ۵
  ارائه شود؛ explanation و contact MUST NOT اجباری یا جمع‌آوری شود.
- **FR-033**: برای هر guest owner + analysis + current report revision حداکثر یک rating جاری MAY وجود داشته
  باشد؛ کاربر MUST بتواند آن را تغییر یا حذف کند و deletion analysis MUST rating را نیز حذف کند.
- **FR-034**: هر retry که report mode یا هر prose/evidence/outcome قابل‌مشاهده را تغییر دهد MUST report revision
  تازه و rating خالی بسازد؛ payload و mode دقیقاً یکسان MAY همان revision/rating را حفظ کند. rating revision قبلی
  MUST NOT به محتوای متفاوت منتقل شود.
- **FR-035**: feedback MUST report mode را (`AI_ASSISTED_SUCCESS`, `MOCK_ASSISTED` یا `RULE_BASED_LIMITED`) نگه دارد؛ هیچ
  analytics dashboard یا external analytics SDK در این slice مجاز نیست.
- **FR-036**: تنها metric این slice MUST average ratingهای submitted و currently retained، همراه response
  count و breakdown بر اساس report mode باشد؛ MUST NOT کاهش regret یا causal purchase outcome ادعا کند.

### Key Entities

- **Guest Context**: مرز ownership همان browser؛ identity نیست.
- **Analysis**: creation/expiry ثابت، latest answer state، status و current revision pointer.
- **Answer Set**: product fields، شش core و حداکثر سه follow-up با stable ID.
- **Evidence Item**: statement، attribution و source answer/rule.
- **Rubric Result**: `PDA-CAT-v0.3`، dimensionها، matched rules، ordered precedence و scoped outcome.
- **Report Revision**: logical ID، mode، current/stale state و report؛ full revision history لازم نیست.
- **Usefulness Rating**: optional integer 1..5 متعلق به guest owner + analysis + current revision + report mode.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ۱۰۰٪ ordinary pathها هشت primary input field و ۱۰۰٪ longest pathها حداکثر یازده
  question/input prompt دارند؛ completion time بعداً اندازه‌گیری می‌شود و در این فاز result measured نیست.
- **SC-002**: ۱۰۰٪ worked scenarioها سه conclusion justification، budget و target fit را بدون suitability
  overclaim نشان می‌دهند.
- **SC-003**: تمام zero/unknown/invalid money نمونه‌ها behavior متمایز دارند و هیچ division by zero ندارند.
- **SC-004**: normalized input + rubric version یکسان همیشه matched rules و outcome یکسان می‌دهد.
- **SC-005**: ۱۰۰٪ unsupported/contradictory AI outputs rejected یا limited-failure می‌شوند، نه successful.
- **SC-006**: در edit، rating revision قدیمی هرگز روی revision جدید ظاهر نمی‌شود؛ change/remove/delete rating
  behavior صریح است.
- **SC-007**: expired/deleted item از direct access unavailable است و late result آن را resurrect نمی‌کند.
- **SC-008**: requirement، question، rule، scenario و acceptance IDها resolve و mapping همه FRها را پوشش می‌دهد.

## Decisions, assumptions and deferrals

### Product-lead decisions supplied for Phase 1.1

- retention ۹۰روزه non-sliding با lifecycle تعریف‌شده پذیرفته شده است.
- categorical outcomes first slice و rubric `PDA-CAT-v0.3` پیاده و در M1 پذیرفته شده‌اند؛ numerical score
  deferred است. Phase 4 فقط رابط و browser verification مربوط به M2 را مجاز می‌کند.
- M3 یک adapter واقعی و harness ارزیابی را مجاز می‌کند؛ live run فقط در region پشتیبانی‌شده، با credential محلی و
  budget صریح مجاز است. نبود هرکدام باید دقیقاً «live evaluation pending» گزارش شود.
- usefulness feedback حداقلی به first slice بازگشته است.

### Unvalidated assumptions

- مسئله، مخاطب و usefulness واقعی flow هنوز با user research یا usage production اعتبارسنجی نشده‌اند.
- rating usefulness فقط self-report است و evidence کاهش regret یا causal outcome نیست.

### Deployment-phase dependency

- backup retention/erasure lifecycle باید پیش از production readiness مشخص شود؛ این spec erasure فوری backup
  ادعا نمی‌کند.
