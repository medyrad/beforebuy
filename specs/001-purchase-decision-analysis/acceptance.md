# Written acceptance criteria

این acceptanceها برای product review هستند؛ automated application test محسوب نمی‌شوند. requirementهای
authoritative همان `FR-*` در [spec](spec.md) هستند.

## Journey and questionnaire

### `AC-JRN-001` — guest Persian flow
**Given** کاربر account ندارد، **When** analysis گوشی را شروع می‌کند، **Then** interface فارسی/RTL بدون
registration قابل تکمیل است.

### `AC-JRN-002` — exact burden
**Given** مسیر عادی است، **When** ورودی‌ها تکمیل می‌شوند، **Then** دو product field و شش core answer یعنی
هشت primary input field وجود دارد؛ **And** longest path با pool مشترک سه follow-up حداکثر یازده
question/input prompt دارد؛ **And** این count تعداد tap/keystroke یا completion time measured نیست.

### `AC-JRN-003` — no duplicate collection
**Given** questionnaire نمایش داده می‌شود، **When** fieldها شمرده می‌شوند، **Then** reason و expected benefit
در `Q-002` ادغام شده‌اند و income/debt/identity/contact یا current-device-name field وجود ندارد.

## Money validation

### `AC-VAL-001` — equivalent digits/grouping
**Given** `۱۲٬۵۰۰٬۰۰۰`، `12,500,000`، `12 500 000` و `۱۲۵۰۰۰۰۰` در context صریح تومان، **When** normalize
می‌شوند، **Then** همگی `12500000` تومان‌اند.

### `AC-VAL-002` — price business validity
**Given** price صفر، منفی، decimal، scientific notation، malformed grouping یا currency دیگر است، **When**
validation اجرا می‌شود، **Then** report ساخته نمی‌شود و پیام class-specific با نمونه تومان نمایش می‌یابد.

### `AC-VAL-003` — zero budget
**Given** price صحیح مثبت و budget = 0، **When** rubric اجرا می‌شود، **Then** `ABOVE_BUDGET` و delta برابر
price است؛ **And** division/ratio انجام نمی‌شود.

### `AC-VAL-004` — unknown is not zero
**Given** budget = `UNKNOWN`، **When** rubric اجرا می‌شود، **Then** `BUDGET_UNKNOWN` است و نه zero یا
`WITHIN_BUDGET`; **And** budget منفی با پیام actionable رد می‌شود.

## Scoped conclusions and evidence

### `AC-RUB-001` — phone purchase supported, product unverified
**Given** گوشی unusable، benefit ضروری، price within و target capability unknown است، **When** report تولید
می‌شود، **Then** outcome `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` و headline می‌گوید خرید/تعویض گوشی موجه و
price در budget است، ولی مناسب‌بودن این مدل تأیید نشده است.

### `AC-RUB-002` — discretionary choice
**Given** گوشی سالم، benefit enjoyment، price within و tradeoff acknowledged است، **When** report تولید
می‌شود، **Then** `DISCRETIONARY_CHOICE_WITHIN_BUDGET` بدون diagnosis یا product suitability claim است.

### `AC-RUB-003` — critical target unknown
**Given** مشکل serious و benefit major با evidence روشن، price within، gaming critical و target capability
unknown است، **When** report ساخته می‌شود، **Then** outcome
`PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` همراه `TARGET_FIT_UNVERIFIED` prominent است؛ **And** suitability همین
مدل تأیید نمی‌شود.

### `AC-RUB-004` — urgent above budget
**Given** replacement ضروری و فوری و price بالاتر از budget است، **When** rubric اجرا می‌شود، **Then**
`BUDGET_MISMATCH` headline است و need/urgency و target-fit unknown در summary مجاور باقی می‌مانند.

### `AC-RUB-005` — contextual insufficiency only
**Given** justification evidence unresolved یا contradictory است ولی budget معلوم است، **When** report ساخته
می‌شود، **Then** `INSUFFICIENT_CONTEXT` فقط همان conclusion را محدود و budget/target states را حفظ می‌کند.

### `AC-RUB-006` — deterministic repeatability
**Given** normalized inputs و rubric `PDA-CAT-v0.3` یکسان‌اند، **When** analysis تکرار می‌شود، **Then**
dimensionها، matched rules، precedence و outcome یکسان‌اند و prose نتیجه را تغییر نمی‌دهد.

### `AC-RUB-007` — considered alternative does not override
**Given** justification supported، price within و repair/wait فقط noted است، **When** outcome انتخاب می‌شود،
**Then** `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` باقی می‌ماند؛ **And** alternative فقط suggestion برای
investigation است، نه evidence feasibility/preference.

### `AC-RUB-008` — total ordered selection
**Given** هر ترکیب input معتبر، **When** dimensionها و جدول `OUT-01..10` به‌ترتیب ارزیابی می‌شوند، **Then**
هر dimension دقیقاً یک status و analysis دقیقاً یک primary outcome دارد؛ **And** multiple match با first-match
precedence حل و matched rule list برای explanation حفظ می‌شود.

### `AC-EVD-001` — traceable claims
**Given** report claim دارد، **When** reviewer آن را بررسی می‌کند، **Then** claim به answer ID، evidence item یا
deterministic rule و یکی از چهار attribution مجاز پیوند دارد.

### `AC-EVD-002` — no inferred product facts
**Given** فقط model name و user answers موجود است، **When** report ساخته می‌شود، **Then** capability، market
value یا price competitiveness به‌عنوان verified نمایش داده نمی‌شود؛ user-reported support نیز verified نیست.

## AI boundary

### `AC-AI-001` — unsupported output rejected
**Given** AI claim بی‌source، evidence ID نامرتبط، product fact استنتاجی یا outcome متناقض تولید می‌کند،
**When** source ID و content/type evidence validate می‌شوند، **Then** successful report نیست و claim نمایش
داده نمی‌شود.

### `AC-AI-002` — limited fallback
**Given** AI output رد/timeout/malformed شده ولی deterministic result موجود است، **When** result منتشر
می‌شود، **Then** mode `RULE_BASED_LIMITED`، retry state و فقط claimهای rule-grounded دارد؛ در نبود result،
report/history entry ایجاد نمی‌شود.

### `AC-AI-003` — user text is data
**Given** answer کاربر شامل دستور تغییر policy/rule است، **When** پردازش می‌شود، **Then** فقط data تلقی و
instruction نادیده گرفته می‌شود.

### `AC-AI-004` — live boundary
**Given** فقط mock وجود دارد یا limits/evaluation/provider واقعی تعیین نشده، **When** readiness review انجام
می‌شود، **Then** محصول live-ready نامیده نمی‌شود؛ **And** mock report برابر `MOCK_ASSISTED` است و rating آن در
breakdown `AI_ASSISTED_SUCCESS` شمرده نمی‌شود.

### `AC-AI-005` — independent evaluation evidence
**Given** output ساختاری معتبر است ولی semantic review انسانی انجام نشده، **When** artifact ارزیابی ساخته می‌شود،
**Then** structural validity، outcome equality و unknown preservation مستقل ثبت می‌شوند؛ **And** semantic support،
readability، actionability و added usefulness برابر `null/pending` می‌مانند؛ **And** overall success ادعا نمی‌شود.

### `AC-AI-006` — value-aware claim support
**Given** claim مثبت target fit به evidence معتبر از نظر ID اشاره می‌کند، **When** value آن unknown، negative یا
contradictory است یا attribution آن user-reported نیست، **Then** validator claim را رد می‌کند؛ **And** فقط value مثبت
صریح با wording user-reported قابل قبول است. متن آزاد نامرتبط یا عدد/alternative ساختگی همچنان نیازمند review انسانی است.

### `AC-AI-007` — complete conservative cost ledger
**Given** live call با schema/instructions و retry bound رزرو شده، **When** usage واقعی، retry یا usage نامعلوم settle
می‌شود، **Then** reservation کل request را پوشش می‌دهد، settlement تکراری دوباره charge نمی‌کند، usage واقعی clip
نمی‌شود و discrepancy/unknown conservatively ثبت می‌شود؛ **And** network بیرون transaction می‌ماند.

### `AC-AI-008` — Iran provider eligibility and direct-adapter isolation
**Given** backend و کاربران اولیه در ایران هستند، **When** live generator انتخاب می‌شود، **Then** direct OpenAI
هیچ‌گاه انتخاب نمی‌شود و تنها AvalAI با credential مستقل، eligibility gate مستقل و مدل دقیق مصوب قابل انتخاب است.

### `AC-AI-009` — documented AvalAI Responses contract
**Given** stub سازگار با AvalAI، **When** adapter فراخوانی می‌شود، **Then** `/v1/responses`،
`gpt-5.6-luna`، JSON Schema strict، `store=false`، timeout، usage و `avalai-request-id` طبق قرارداد مستند مصرف
می‌شوند؛ malformed، timeout، 429 و خطای دائمی fail closed هستند.

### `AC-AI-010` — total toman evaluation cap
**Given** تعرفهٔ AvalAI، exchange rate تازه و margin محافظه‌کارانه، **When** dataset هفت‌تایی preflight می‌شود،
**Then** کل requestها و retryها پیش از call در cap صریح حداکثر ۱۰۰٬۰۰۰ تومان جا می‌گیرند یا هیچ call مدل انجام
نمی‌شود؛ گزارش هزینه estimate را از invoice قطعی جدا می‌کند.

### `AC-AI-011` — independent persistent budget scopes
**Given** deployment day changes or evaluation process restarts/concurrently resumes, **When** a case reserves cost,
**Then** deployment daily window and the single initial 100,000-toman authorization are both checked atomically؛ **And**
evaluation spent + outstanding reservation never resets at midnight or process start.

### `AC-AI-012` — pre-call rejection is evidence, not a call
**Given** deployment budget، guest quota یا circuit پیش از invocation مانع است، **When** runner case را اجرا می‌کند،
**Then** attempt/call/usage برابر صفر، skip reason ساختاریافته و run status ناقص است؛ **And** lookup نبود invocation crash نمی‌کند.

### `AC-AI-013` — atomic partial checkpoint
**Given** چند case تکمیل شده و process در case بعد قطع می‌شود، **When** artifact خوانده می‌شود، **Then** caseهای تکمیل‌شده،
last completed، remaining IDs، operation/request metadata امن و `incomplete` باقی است؛ **And** raw transport/secret وجود ندارد.

### `AC-AI-014` — per-attempt honest settlement and recovery
**Given** retry با usage معلوم/نامعلوم، malformed response، duplicate settlement یا reservation رهاشده، **When** settle/recover
می‌شود، **Then** known usage کامل جمع، unknown محافظه‌کارانه، overage visible و underflow خطاست؛ **And** recovery invoice قطعی ادعا نمی‌کند.

### `AC-AI-015` — separated evaluation gates and valid money
**Given** تعرفهٔ `$30/M` output مدل منتخب، **When** policy v1.2 ارزیابی می‌شود، **Then** incompatibility آستانهٔ تاریخی
`$0.0025` مستقل از total spend/structure/human/latency ثبت و overall pending است؛ **And** non-finite/negative monetary values
پیش از هر network call رد می‌شوند.

### `AC-UI-001` — concise Persian result
**Given** report روی viewport desktop یا mobile نمایش داده می‌شود، **When** کاربر summary، reasons، mode و feedback را
می‌خواند، **Then** متن طبیعی و scoped است، ابهام مدل برجسته است، چهار dimension در mobile یک card با چهار row است،
و ratingهای ۱ و ۵ به‌ترتیب label دسترس‌پذیر «اصلاً کمک نکرد» و «خیلی کمک کرد» دارند.

## Revision and feedback

### `AC-EDT-001` — stale and new revision
**Given** report جاری وجود دارد، **When** input مؤثر edit می‌شود، **Then** report/evidence/prose قبلی stale و
input revision تازه با همان rubric version از latest answers recompute می‌شود.

### `AC-EDT-002` — late response cannot overwrite
**Given** generation برای input revision قدیمی در جریان است، **When** edit/delete/expiry رخ می‌دهد و response
دیررس می‌رسد، **Then** response publish نمی‌شود و current result/rating/history را overwrite یا resurrect نمی‌کند.

### `AC-FBK-001` — optional prompt
**Given** report جاری نمایش داده شده، **When** feedback prompt دیده می‌شود، **Then** متن آن «این تحلیل چقدر
به تصمیم شما کمک کرد؟» و response اختیاری integer 1..5 است؛ explanation/contact خواسته نمی‌شود.

### `AC-FBK-002` — one mutable rating
**Given** rating برای guest + analysis + current revision وجود دارد، **When** دوباره rating ثبت، تغییر یا حذف
می‌شود، **Then** حداکثر یک current rating باقی می‌ماند یا هیچ rating وجود ندارد.

### `AC-FBK-003` — no carry-forward
**Given** revision `r1` rating دارد، **When** edit باعث revision `r2` می‌شود، **Then** `r2` بدون rating آغاز و
rating `r1` به آن attach نمی‌شود؛ full revision history persist نمی‌شود.

### `AC-FBK-004` — report mode and metric
**Given** ratingهای retained برای modeهای مختلف وجود دارند، **When** metric گزارش می‌شود، **Then** فقط average،
response count و report-mode breakdown دارد؛ causal regret/purchase outcome ادعا و dashboard/SDK ایجاد نمی‌شود.

### `AC-FBK-005` — retry changes report content or mode
**Given** report rating دارد، **When** retry هر prose/evidence/outcome قابل‌مشاهده یا report mode را تغییر می‌دهد،
**Then** report revision تازه بدون rating ایجاد می‌شود؛ **And** payload و mode دقیقاً یکسان rating را به محتوای
متفاوت منتقل نمی‌کند.

## Ownership, retention and deletion

### `AC-HIS-001` — guest isolation
**Given** guest B analysis ID مهمان A را می‌داند، **When** direct access می‌خواهد، **Then** بدون ownership
context دسترسی ندارد؛ cross-device/public recovery وعده داده نمی‌شود.

### `AC-HIS-002` — creation anchor
**Given** نخستین persisted result یک successful یا limited report در T0 است، **When** lifecycle تعیین می‌شود،
**Then** creation = T0 است؛ failure بدون report creation ایجاد نمی‌کند.

### `AC-HIS-003` — non-sliding expiry
**Given** visit، feedback، retry یا edit همان analysis رخ می‌دهد، **When** expiry محاسبه می‌شود، **Then** همان
T0 + 90 days باقی می‌ماند؛ analysis عمداً جدید anchor مستقل دارد.

### `AC-HIS-004` — expiry and purge
**Given** زمان expiry رسیده، **When** history/direct URL باز می‌شود، **Then** فوراً unavailable است؛ **And**
active-storage purge تا ۲۴ ساعت بعد target می‌شود، بدون ادعای erasure فوری backup.

### `AC-HIS-005` — delete one/all and rating
**Given** guest مالک analysis است، **When** یک analysis یا all history را حذف می‌کند، **Then** direct/history
access و ratingهای مربوط حذف می‌شوند و context مهمان دیگر متاثر نیست.

### `AC-HIS-006` — delete during retry
**Given** generation/retry in-flight است، **When** analysis حذف و سپس late result می‌رسد، **Then** result/rating
discard می‌شود و analysis resurrect نمی‌شود.

### `AC-HIS-007` — minimal persistence
**Given** analysis persist می‌شود، **When** stored state بررسی می‌شود، **Then** فقط latest required inputs,
normalized money، current report/evidence/rubric/revision/rating، mode و lifecycle timestamps وجود دارند؛ نه
full revision history، identity/contact/fingerprint یا raw provider prompt/response.

### `AC-HIS-008` — anonymous guest CSRF
**Given** guest session معتبر دارد، **When** هر unsafe operation را بدون token یا با token نامعتبر می‌فرستد،
**Then** `CsrfViewMiddleware`/`csrf_protect` استاندارد Django آن را با `403` رد می‌کند؛ **And** token صحیح از bootstrap
same-origin پذیرفته می‌شود؛ **And** host/origin نامجاز مطابق config deployment رد می‌شود.

### `AC-HIS-009` — late-created analysis remains accessible
**Given** guest روز صفر bootstrap و روز ۸۹ analysis جدید persist می‌کند، **When** cookie/session توسط browser حفظ شده،
**Then** access lifetime تا expiry روز ۱۷۹ آن analysis تمدید می‌شود؛ **And** visit/edit/retry/feedback expiry خود analysis
را تغییر نمی‌دهند؛ **And** cookie loss recovery ندارد.

### `AC-HIS-010` — clear invalidates in-flight initial create
**Given** initial create epoch `e` را گرفته و هنوز Analysis row ندارد، **When** clear-history epoch را در transaction
به `e+1` افزایش و current data را حذف می‌کند، **Then** create قدیمی publish نمی‌شود؛ create جدید بعد clear مجاز است.

### `AC-HIS-011` — competing retries publish newest operation only
**Given** دو retry روی input revision یکسان شروع می‌شوند، **When** retry دوم operation token جدیدتری ثبت می‌کند و
responseها خارج از ترتیب می‌رسند، **Then** فقط token جاری report/rating را replace می‌کند و پاسخ قدیمی conflict/discard است.

## Requirement → scenario → acceptance mapping

| Requirements | Scenarios | Acceptance criteria |
|---|---|---|
| `FR-001..FR-003` | `SYN-001`, `SYN-002` | `AC-JRN-001..003` |
| `FR-004..FR-006` | `SYN-006` | `AC-VAL-001..004` |
| `FR-007..FR-009` | `SYN-001..SYN-005` | `AC-JRN-002..003` |
| `FR-010..FR-014` | `SYN-001..SYN-010` | `AC-RUB-001..005`, `AC-EVD-001..002` |
| `FR-015..FR-019` | `SYN-001..SYN-009` | `AC-RUB-001..008` |
| `FR-020..FR-023`, `FR-037..FR-044` | `SYN-010` | `AC-AI-001..010` |
| `FR-024..FR-031` | `SYN-011`, `SYN-012` | `AC-EDT-001..002`, `AC-HIS-001..011` |
| `FR-032..FR-036` | `SYN-011`, `SYN-012` | `AC-FBK-001..005`, `AC-HIS-005` |
| `FR-040` | `SYN-001`, `SYN-011` | `AC-UI-001`, `AC-FBK-001` |

## Review boundary

rubric `PDA-CAT-v0.3` با direction Phase 2 برای technical planning پذیرفته است؛ این acceptanceها مجوز
implementation نیستند. backup lifecycle هنوز readiness gate فاز deployment است.
