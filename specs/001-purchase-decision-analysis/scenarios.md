# Synthetic acceptance scenarios

این ۱۲ scenario برای review requirement/rubric هستند؛ user research، measured completion result یا automated
application test نیستند. هر run input معتبر دارد و دقیقاً یک primary outcome انتظار می‌رود.

## `SYN-001` — supported purchase، budget fits، model unverified

- **Inputs**: `UNUSABLE`؛ `RESTORE_ESSENTIAL_ACCESS`؛ price ۲۰ و budget ۲۵ میلیون تومان؛ target unknown.
- **Dimensions**: `JUSTIFICATION_SUPPORTED`, `WITHIN_BUDGET`, `TARGET_FIT_UNVERIFIED`, `NOT_REQUIRED`.
- **Rules/outcome**: `JUS-04`, `BUD-01`, `FIT-03`, `OUT-08` → `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET`.
- **Headline**: «خرید یا تعویض گوشی با توجه به وضعیت فعلی قابل توجیه است و قیمت واردشده در محدوده بودجه
  شماست؛ مناسب‌بودن این مدل هنوز تأیید نشده است.»

## `SYN-002` — working device + important new use

- **Inputs**: `WORKS_WELL`؛ `ENABLE_IMPORTANT_NEW_USE`؛ price within؛ target capability unknown.
- **Dimensions/outcome**: `JUSTIFICATION_SUPPORTED`, `WITHIN_BUDGET`, `TARGET_FIT_UNVERIFIED` → `OUT-08`.
- **Boundary**: working device positive justification را منع نمی‌کند، اما target capability را ثابت نمی‌کند.

## `SYN-003` — minor problem + clear minor benefit

- **Inputs**: `MINOR_PROBLEM`؛ `SOLVE_MINOR_LIMIT`؛ price within؛ `ACCEPTED_TARGET_TRADEOFFS`.
- **Dimensions/outcome**: `DISCRETIONARY_CLEAR`, `WITHIN_BUDGET`, `ACKNOWLEDGED` → `OUT-09` →
  `DISCRETIONARY_CHOICE_WITHIN_BUDGET`.
- **Boundary**: benefit روشن است، اما necessity یا technical suitability ادعا نمی‌شود.

## `SYN-004` — unresolved justification

- **Run A**: `SERIOUS_PROBLEM` + benefit `UNKNOWN` پس از follow-up → `JUSTIFICATION_UNKNOWN` → `OUT-02` →
  `INSUFFICIENT_CONTEXT`.
- **Run B**: current-device state `UNKNOWN` + major benefit پس از follow-up → همان outcome.
- **Boundary**: known budget و target-fit status همچنان نمایش داده می‌شوند؛ missing به `WEAK_OR_NONE` تبدیل نمی‌شود.

## `SYN-005` — enjoyment and tradeoff boundary

- **Run A**: device known؛ `PERSONAL_ENJOYMENT`؛ tradeoff unknown/unacknowledged؛ budget within → `TRD-02` +
  `OUT-05` → `INSUFFICIENT_CONTEXT`.
- **Run B**: `NO_DEVICE`؛ `PERSONAL_ENJOYMENT`؛ `ACCEPTED_TARGET_TRADEOFFS`؛ budget within → `JUS-03`,
  `TRD-01`, `OUT-09` → `DISCRETIONARY_CHOICE_WITHIN_BUDGET`.
- **Boundary**: no device به‌تنهایی necessity نمی‌سازد؛ enjoyment diagnosis یا failure نیست.

## `SYN-006` — zero budget versus unknown budget

- **Run A**: price ۱۲ میلیون، budget `ZERO` → `BUD-02`, delta ۱۲ میلیون، `ABOVE_BUDGET`؛ بدون division.
- **Run B**: همان price، budget `UNKNOWN` + justification supported → `BUD-03`, `OUT-06` →
  `PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN`.
- **Run C**: price `0` یا budget منفی → `VAL-01/02` و message actionable؛ report ساخته نمی‌شود.

## `SYN-007` — unknown budget with weak or contradictory justification

- **Run A**: budget unknown + known state + `NO_CLEAR_BENEFIT` → `JUS-05`, `OUT-04` → `RECONSIDER_OR_WAIT`؛
  budget unknown visible است.
- **Run B**: budget unknown + unresolved contradiction → `JUS-01`, `OUT-02` → `INSUFFICIENT_CONTEXT`.
- **Boundary**: outcome table ordered است؛ budget unknown positive affordability claim تولید نمی‌کند.

## `SYN-008` — user-reported target mismatch

- **Inputs**: justification supported؛ budget within؛ `F-003 = USER_REPORTS_IT_DOES_NOT_FIT`.
- **Dimensions/outcome**: `USER_REPORTED_MISMATCH` + `OUT-03` → `RECONSIDER_OR_WAIT`.
- **Headline**: «خرید یا تعویض گوشی از نظر وضعیت و بودجه قابل توجیه است؛ اما طبق اطلاعاتی که شما ارائه
  کردید، این مدل نیاز اصلی را پوشش نمی‌دهد، پس انتخاب مدل را بازبینی کنید.»
- **Boundary**: mismatch user-reported است، نه verified external fact.

## `SYN-009` — above budget and multiple matches

- **Inputs**: `UNUSABLE`، essential benefit، price ۳۰ و budget ۱۸ میلیون، target mismatch، repair noted.
- **Dimensions**: justification supported، above budget، user-reported mismatch؛ `REPAIR_NOTED`.
- **Outcome**: چند rule match می‌شوند، اما ordered `OUT-01` فقط `BUDGET_MISMATCH` را primary می‌کند؛ سایر
  dimensionها/concernها visible می‌مانند. repair noted outcome را override نمی‌کند.

## `SYN-010` — unsupported or contradictory AI output

- **Inputs**: deterministic result موجود؛ AI product fact بی‌پشتوانه می‌سازد یا evidence ID نامرتبط ارائه می‌دهد.
- **Expected**: claim/content compatibility validation fail؛ output successful نیست؛ `RULE_BASED_LIMITED` برای
  current input revision یا failure بدون report. user text instruction تلقی نمی‌شود.

## `SYN-011` — edit, retry and feedback ownership

- **Inputs**: report `r1` برای input revision `i1` rating ۴ دارد؛ edit → `i2`; response دیررس `i1` می‌رسد؛
  retry `i2` mode/prose را تغییر می‌دهد.
- **Expected**: response `i1` discard؛ result `i2` با همان rubric version recompute؛ تغییر payload/mode report
  revision `r2` و rating خالی می‌سازد. retry payload+mode دقیقاً یکسان revision/rating را تغییر نمی‌دهد.

## `SYN-012` — retention expiry and deletion during retry

- **Inputs**: first persisted limited report در T0؛ visit/edit/retry؛ سپس delete یا expiry حین generation.
- **Expected**: expiry = T0 + 90 days؛ reset نمی‌شود؛ direct access unavailable؛ active purge تا ۲۴ ساعت؛
  late result/rating discard و resurrection ممنوع؛ backup erasure فوری ادعا نمی‌شود.
