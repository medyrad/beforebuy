# Choice Desk Design Specification — Concept 2

## Authorized UX refinement (2026-11-16)

Two-pass direction: warm paper `#f6f4ef`, white surfaces, ink `#24332f`, muted `#59645f`, indigo `#4b46a5`,
teal `#25675b`; existing self-hosted Vazirmatn and original SVG line icons, no product photography. Desktop right
chat / left contextual desk; compact top navigation. Homepage hero «برای چه خریدی کمکت کنم؟», six prompt categories,
working first-message composer, examples and continuation. Desk initially shows the next step, then «نیاز خرید شما»,
«گزینه‌های پیشنهادی», «مقایسه», «از کجا بخرم؟» as evidence/confirmation becomes available.

Critique against brief: avoid empty dashboard cards and technical forms before useful data; no fake market coverage.
Chat is a min-height:0 flex column inside the remaining viewport, with independent thread scroll and bounded composer.
Mobile is chat-first with explicit desk switch; history uses a labelled modal drawer, Escape/focus return and explicit
destructive confirmation. Near-bottom following only; reading above gets «پیام‌های جدید». No global overflow masking.
Settings/profile preserve mounted chat state. Saved, validated, selected provider/model and effective mode are distinct.
Visual acceptance remains pending product-lead review even when automated checks pass.

Choice Desk فضای آرام تحلیلی است، نه storefront. conversation brief می‌سازد؛ Desk evidence/tradeoff را مقایسه می‌کند. visual language باید دقیق، فارسی‌اول و شبیه یک workspace تصمیم‌گیری باشد، نه dashboard generic.

## Historical baseline information architecture (superseded where specified above)

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
