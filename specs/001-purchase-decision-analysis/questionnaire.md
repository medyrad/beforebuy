# پرسش‌نامه حداقلی تحلیل تصمیم خرید

**Status**: M1 contract پیاده؛ triggerهای نمایش M2 در Phase 4 بسته شده‌اند  
**Scope**: هشت primary input field و حداکثر سه follow-up شرطی در کل flow  
**Evidence rule**: تمام پاسخ‌ها `USER_REPORTED` هستند؛ نام مدل باعث lookup یا استنتاج capability نمی‌شود.

## بار واقعی کاربر

- مسیر عادی: **۸ primary input field**؛ دو field محصول (`PC-001..002`) + شش core question (`Q-001..006`).
- طولانی‌ترین مسیر: **تا ۱۱ question/input prompt**؛ همان ۸ field + حداکثر سه follow-up از pool واحد
  (`F-001..003`).
- این count تعداد field/prompt است، نه تعداد tap/keystroke؛ multi-select می‌تواند چند action بخواهد. گزینه
  `OTHER` در این slice field اضافه باز نمی‌کند و allowance جداگانه‌ای برای AI و rule وجود ندارد.
- نام دستگاه فعلی، income، debt، identity، contact و توضیح اجباری feedback جمع‌آوری نمی‌شوند.

## Product entry

| ID | wording فارسی | Input / allowed values | Required | «نمی‌دانم» | Validation / visibility | مصرف‌کننده |
|---|---|---|---|---|---|---|
| `PC-001` | «چه تلفنی را برای خرید در نظر دارید؟» | متن کوتاه، ۲ تا ۱۲۰ نویسه | بله | خیر؛ یک description قابل تشخیص لازم است | trim؛ فقط whitespace نامعتبر؛ همیشه visible | عنوان report؛ بدون استنتاج مشخصات |
| `PC-002` | «قیمت تقریبی این خرید چند تومان است؟» | positive whole toman amount؛ رقم فارسی/لاتین و grouping مجاز | بله | خیر | بزرگ‌تر از صفر؛ label صریح «تومان»؛ همیشه visible | `BUD-01..02` و Budget fit |

## Core questions

| ID | wording فارسی | Input / allowed values | Required | «نمی‌دانم» | Validation | Rule / report section |
|---|---|---|---|---|---|---|
| `Q-001` | «وضعیت گوشی فعلی شما کدام است؟» | single select: `NO_DEVICE`, `UNUSABLE`, `SERIOUS_PROBLEM`, `MINOR_PROBLEM`, `WORKS_WELL`, `UNKNOWN` | بله | `UNKNOWN` | همیشه visible؛ یک value | `JUS-01..06`؛ Purchase justification |
| `Q-002` | «مهم‌ترین نتیجه‌ای که از این خرید انتظار دارید چیست؟» | single select: `RESTORE_ESSENTIAL_ACCESS`, `SOLVE_MAJOR_LIMIT`, `ENABLE_IMPORTANT_NEW_USE`, `SOLVE_MINOR_LIMIT`, `PERSONAL_ENJOYMENT`, `NO_CLEAR_BENEFIT`, `UNKNOWN` | بله | `UNKNOWN` | همیشه visible؛ reason و expected benefit را در یک evidence item جمع می‌کند | `JUS-01..06`؛ rationale |
| `Q-003` | «این تلفن را بیشتر برای چه کارهایی می‌خواهید؟» | multi-select حداکثر ۳: `CALLS_MESSAGES`, `PHOTO_VIDEO`, `WORK_STUDY`, `GAMING`, `ACCESSIBILITY`, `GENERAL_USE`, `OTHER`, `UNKNOWN` | بله | `UNKNOWN` به‌تنهایی | ۱ تا ۳ value؛ `OTHER` فیلد اضافه ندارد | Usage clarity؛ Target fit |
| `Q-004` | «چه زمانی به این خرید نیاز دارید؟» | single select: `WITHIN_48_HOURS`, `WITHIN_2_WEEKS`, `WITHIN_3_MONTHS`, `FLEXIBLE`, `UNKNOWN` | بله | `UNKNOWN` | همیشه visible | Urgency؛ actionها |
| `Q-005` | «حداکثر بودجه شما برای این خرید چند تومان است؟» | `ZERO`، positive whole toman amount، یا `UNKNOWN` | بله | `UNKNOWN` یک state صریح است، نه عدد صفر | label صریح «تومان»؛ منفی/اعشار/notation/ارز مبهم invalid | `BUD-01..03`؛ Budget fit |
| `Q-006` | «کدام گزینه‌ها یا tradeoffها را واقعاً بررسی کرده‌اید؟» | multi-select: `REPAIR_CURRENT`, `WAIT`, `KEEP_CURRENT`, `CHANGE_REQUIREMENTS`, `ACCEPTED_TARGET_TRADEOFFS`, `NONE`, `UNKNOWN` | بله | `UNKNOWN` به‌تنهایی | `NONE` و `UNKNOWN` با گزینه دیگر جمع نمی‌شوند | `TRD-01..03`؛ alternatives / acknowledged tradeoffs |

## Conditional follow-up pool

این سه ID یک pool مشترک‌اند. rule deterministic یا AI می‌تواند فقط wording مبتنی بر trigger را پیشنهاد کند،
اما مجموع سؤال‌های نمایش‌داده‌شده در تمام flow هرگز از سه بیشتر نیست. سؤال فقط وقتی نمایش داده می‌شود که پاسخ
آن conclusion یا unknown consequential را تغییر دهد. unresolved item با حدس پر نمی‌شود.

| Priority / ID | Trigger | wording فارسی | Input | Required | اثر «نمی‌دانم» / مصرف‌کننده |
|---|---|---|---|---|---|
| 1 / `F-001` | `Q-001` و `Q-002` ناسازگارند، یا وضعیت `SERIOUS_PROBLEM` برای justification به evidence روشن نیاز دارد | «برای روشن‌شدن وضعیت فعلی، مشکل اصلی گوشی فعلی یا دلیل نبود گوشی را در یک جمله بگویید.» | متن حداکثر ۲۴۰ نویسه یا `STILL_UNKNOWN` | خیر | unresolved contradiction consequential → `INFO-02`؛ در غیر این صورت evidence نیاز |
| 2 / `F-002` | نتیجهٔ مورد انتظار `Q-002` برابر `UNKNOWN` است | «کدام نتیجه به تصمیم فعلی شما نزدیک‌تر است؟» | انتخاب از valueهای غیر-`UNKNOWN` همان `Q-002` یا `STILL_UNKNOWN` | خیر | انتخاب مشخص، پاسخ `Q-002` را پیش از submit روشن می‌کند؛ `STILL_UNKNOWN` unknown را حفظ می‌کند → `INFO-01` |
| 3 / `F-003` | یک استفاده critical مثل gaming/accessibility/workload بیان شده یا کاربر درباره suitability مدل ادعا دارد | «درباره مناسب‌بودن این مدل برای استفاده ضروری‌تان چه اطلاعاتی دارید؟» | `USER_REPORTS_IT_FITS`, `USER_REPORTS_IT_DOES_NOT_FIT`, `NO_INFORMATION` | خیر | `NO_INFORMATION` → `TARGET_FIT_UNVERIFIED`؛ پاسخ مثبت فقط `USER_REPORTED` است، هرگز verified نیست |

اگر بیش از سه clarification candidate پدید آید، priority بالا اعمال و بقیه به‌صورت unknown/actionable question
در report ثبت می‌شوند. allowance دیگری برای follow-upهای AI وجود ندارد.

### Trigger و mapping قطعی برای رابط M2

رابط صرفاً flow پرسش‌نامه را کنترل می‌کند و rubric دوم نمی‌سازد. candidateها با ترتیب ثابت زیر محاسبه و حداکثر
سه مورد اول نمایش داده می‌شوند:

1. `F-001` وقتی `Q-001=SERIOUS_PROBLEM` یا زوج `Q-001/Q-002` عضو contradictionهای مستند `JUS-01` است.
   این متن فقط evidence تکمیلی است؛ در mode mock تناقض categorical را خودکار حل نمی‌کند و رابط کاربر را برای
   اصلاح پاسخ اصلی به مرحلهٔ قبل راهنمایی می‌کند.
2. `F-002` فقط وقتی `Q-002=UNKNOWN` است. انتخاب یک benefit مشخص، همان value را به‌عنوان `Q-002` نهایی می‌فرستد
   و پاسخ `F-002` را نیز برای traceability نگه می‌دارد؛ `STILL_UNKNOWN`، `Q-002=UNKNOWN` را حفظ می‌کند.
3. `F-003` وقتی `Q-003` حداقل یکی از `GAMING`, `ACCESSIBILITY`, `WORK_STUDY` را دارد. پاسخ آن طبق `FIT-01..03`
   مستقیماً target fit را روشن یا نامعلوم نگه می‌دارد.

`Q-004=UNKNOWN` به‌تنهایی follow-up ایجاد نمی‌کند، چون rubric `PDA-CAT-v0.3` urgency را در outcome مصرف نمی‌کند؛
پرسیدن clarification بی‌اثر با اصل minimization ناسازگار است. این mapping presentation/normalization است و
هیچ outcome یا dimension را در browser محاسبه نمی‌کند.

## Money normalization and validation

### Syntax

- رقم‌های فارسی `۰..۹` و لاتین `0..9` پیش از parsing به یک representation تبدیل می‌شوند.
- مقدار بدون grouping یا با grouping سه‌رقمی معتبر توسط `,`، `٬` یا فاصله پشتیبانی می‌شود؛ نمونه‌های معتبر:
  `۱۲٬۵۰۰٬۰۰۰`، `12,500,000`، `12 500 000` و `۱۲۵۰۰۰۰۰`.
- separatorهای مخلوط، grouping ناقص مانند `12,50,000`، علامت، حروف، decimal separator، `e/E` و notation
  scientific malformed هستند و silently اصلاح نمی‌شوند.
- label و help text هر دو field پول صریحاً «تومان» هستند. اگر متن کاربر «ریال»، «دلار» یا currency دیگری
  داشته باشد، مقدار ambiguous currency است؛ conversion انجام نمی‌شود.

### Business circumstances

- price باید **عدد صحیح مثبت تومان** باشد؛ `0` و مقدار منفی برای price نامعتبرند.
- budget می‌تواند `0` تومان، عدد صحیح مثبت تومان یا state صریح `UNKNOWN` باشد. مقدار منفی نامعتبر است.
- budget مفقود/`UNKNOWN` هرگز به صفر normalize نمی‌شود. `0` یک سقف بودجه معلوم و واقعی است.
- برای budget = 0 و هر price معتبر مثبت، `ABOVE_BUDGET` و delta برابر خود price است؛ هیچ division، ratio یا
  درصدی محاسبه نمی‌شود.

### Actionable messages

| Invalid class | پیام موردنیاز |
|---|---|
| price صفر/منفی | «قیمت خرید باید یک عدد صحیح بزرگ‌تر از صفر به تومان باشد؛ نمونه: ۱۲٬۵۰۰٬۰۰۰ تومان.» |
| budget منفی | «بودجه نمی‌تواند منفی باشد؛ صفر تومان یا یک مبلغ صحیح را وارد کنید، یا «نمی‌دانم» را بزنید.» |
| decimal | «مبلغ اعشاری پشتیبانی نمی‌شود؛ مبلغ را به تومان و به‌صورت عدد صحیح وارد کنید.» |
| scientific notation | «نمایش علمی مثل 1e7 پشتیبانی نمی‌شود؛ رقم کامل تومان را وارد کنید.» |
| ambiguous currency | «واحد این جریان تومان است؛ مبلغ را به تومان وارد کنید. تبدیل ارز انجام نمی‌شود.» |
| malformed / bad grouping | «فرمت مبلغ قابل تشخیص نیست؛ نمونه معتبر: ۱۲٬۵۰۰٬۰۰۰ تومان.» |

## Privacy and minimization

- متن آزاد فقط در `PC-001` و follow-up شرطی `F-001` وجود دارد؛ UI از ورود اطلاعات هویتی/حساس منع می‌کند.
- answer source همان user report است. حتی ادعای فنی کاربر `VERIFIED_EXTERNAL` نمی‌شود.
