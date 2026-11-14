# Choice Desk Design Specification — Concept 2

Choice Desk فضای آرام تحلیلی است، نه storefront. conversation brief می‌سازد؛ Desk evidence/tradeoff را مقایسه می‌کند. visual language باید editorial و فارسی‌اول باشد، نه dashboard generic.

## Information architecture

1. conversation rail: thread، composer، attachment، stop، memory status.
2. brief ribbon: budget، recipient، use، hard constraints، unknowns؛ editable/versioned.
3. desk canvas: shortlist 3–6، recommendation مشروط، comparison و evidence drawer.
4. research ledger: progress واقعی، coverage، freshness و failure؛ collapsed by default.

Desktop layout 5/7؛ conversation راست و Desk چپ با DOM order منطقی RTL. Mobile stack با landmarks/tabs «گفت‌وگو / میز انتخاب» و بدون horizontal-scroll ضروری.

## Visual and states

Vazirmatn موجود؛ سطوح گرم خنثی، ink تیره و accent زعفرانی محدود؛ status رنگی همراه text/icon. cards کم؛ desktop table و mobile disclosure. States: empty، clarifying، brief-ready، researching، partial، ready، cancelled، source-limited، AI-blocked، recoverable error. Partial visually final نیست.

## Accessibility/RTL overlay

`lang=fa`, `dir=rtl`; model/URL با `bdi`؛ semantic landmarks/headings، skip link، focus visible، 200% zoom، keyboard. live announcements batch/throttle و قابل توقف؛ delta تک‌تک خوانده نمی‌شود. price تومان label صریح دارد. reduced motion و WCAG AA.

## Skill scope

Anthropic `frontend-design` برای composition/distinctiveness در React+Vite است. این overlay درباره Persian/RTL، accessibility، evidence semantics و ممنوعیت dependencyهای Next.js/Tailwind/shadcn مقدم است.

Verification: 390×844 و 1440×900، keyboard، screen-reader semantics، mixed bidi، long text، slow/error stream و zero serious/critical axe findings.
