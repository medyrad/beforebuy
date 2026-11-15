# Choice Desk Design Specification — Concept 2

Choice Desk فضای آرام تحلیلی است، نه storefront. conversation brief می‌سازد؛ Desk evidence/tradeoff را مقایسه می‌کند. visual language باید دقیق، فارسی‌اول و شبیه یک workspace تصمیم‌گیری باشد، نه dashboard generic.

## Information architecture

1. right-side navigation: brand، مسیر legacy، conversation history و وضعیت fixture.
2. conversation panel on the right: thread، composer، attachment و stop/retry.
3. brief ribbon: budget، recipient، use، hard constraints، unknowns؛ editable/versioned.
4. larger Choice Desk on the left: readiness/empty state در A و shortlist/comparison فقط در milestone C.
5. research ledger: progress واقعی، coverage، freshness و failure؛ از milestone B و collapsed by default.

Desktop تقریباً `5/7` است: conversation در راست و Choice Desk بزرگ‌تر در چپ، با navigation در لبهٔ راست و DOM order منطقی RTL. Mobile navigation میان «گفت‌وگو / میز انتخاب» state هر دو را حفظ می‌کند و دادهٔ ضروری به horizontal scroll وابسته نیست.

## Visual and states

Vazirmatn self-hosted موجود؛ surfaceهای off-white و cool-gray، ink slate و accent indigo محدود. token پایه:
`paper #F7F8FA`، `surface #FFFFFF`، `surface-muted #EEF1F5`، `ink #172033`، `muted #667085`،
`indigo #4F46E5` و `indigo-soft #EEF2FF`. status رنگی همیشه text/icon دارد. SVG iconها باید stroke/size
یکدست، decorative iconها hidden و control iconها label قابل‌دسترسی داشته باشند. cardها کم و hierarchy-driven هستند؛
desktop table و mobile disclosure به Milestone C تعلق دارند.

States: empty، clarifying، brief-ready، generating-fixture، cancelled، interrupted و recoverable error در A؛ researching،
partial، source-limited و choice-ready بعداً. Partial visually final نیست. M1/A فقط empty/readiness صادقانه نشان می‌دهد:
هیچ product card، price، review، rank یا citation ساختگی برای پرکردن Desk وجود ندارد. هر demo صریحاً «fixture توسعه» است.

Shortlist در Milestone C شامل محصول انتخاب‌شدهٔ کاربر، اگر موجود باشد، به‌علاوهٔ حداکثر سه alternative است. merchant
offerها فهرست جدا هستند و recommendation محصول اضافی محسوب نمی‌شوند.

## Accessibility/RTL overlay

`lang=fa`, `dir=rtl`; model/URL با `bdi`؛ semantic landmarks/headings، skip link، focus visible، 200% zoom، keyboard. live announcements batch/throttle و قابل توقف؛ delta تک‌تک خوانده نمی‌شود. price تومان label صریح دارد. reduced motion و WCAG AA.

## Skill scope

Anthropic `frontend-design` برای composition/distinctiveness در React+Vite است. این overlay درباره Persian/RTL، accessibility، evidence semantics و ممنوعیت dependencyهای Next.js/Tailwind/shadcn مقدم است.

Verification: 390×844 و 1440×900، keyboard، screen-reader semantics، mixed bidi، long text، slow/error stream و zero serious/critical axe findings.
