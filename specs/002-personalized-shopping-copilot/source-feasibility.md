# Source Feasibility Register

**Probe**: 2026-11-15؛ یک robots و حداکثر یک page/domain، read-only، redirects ≤3، timeout 8–12s؛ بدون crawl/login/bypass.

| Source | Role/category | Observed policy/response | Extraction evidence | Decision |
|---|---|---|---|---|
| Digikala | Iranian merchant / multi | robots و root در 12s timeout | none | blocked/unassessed؛ no allowlist |
| Torob | Iranian comparison / multi | robots در 12s timeout؛ page بعد آن probe نشد | none | blocked/unassessed |
| Technolife | Iranian merchant / electronics | robots 200؛ `search=yes,ai-train=no,use=reference`, `Allow:/`; root 301 به technolife.com سپس timeout | robots only | conditional؛ redirect/terms/extraction unresolved |
| Apple | manufacturer / electronics | robots 200؛ iPhone 17 specs 200 HTML، 234,076 bytes | model/capacity/dimensions/display observable | manufacturer fixture candidate |
| Philips | manufacturer / appliance | robots 200؛ EP5934 page 200 HTML، 193,393 bytes | voltage/capacity/dimensions/features observable | fixture candidate؛ region/version identity required |
| Nike | manufacturer / sports | robots 200 و `/p/` disallow؛ sample URL 404 HTML، 590,833 bytes | none | reject initial fixture |
| Decathlon | sports | official indexed product with specs | search snippet only، no direct workspace extraction | documentation candidate only |
| Adidas | sports | official indexed product details | search snippet only | fallback after robots/terms/direct probe |

## Coverage conclusion

- electronics و appliance: manufacturer extraction feasibility observed؛ Iranian offer coverage unresolved.
- sports/fashion: official docs surfaced but no successful direct extraction؛ not data-ready.

این probe permission، stability، completeness یا quality benchmark نیست؛ search snippet جای extraction repeatable نیست.

## Domain onboarding

terms/robots snapshot؛ canonical redirect allowlist؛ contact/user-agent؛ small checksum fixture؛ mapping/variant/freshness/failure tests؛ measured rate/byte/cache limits؛ no bypass on 403/429/CAPTCHA/login/paywall.

Proposed test defaults (not production approval): 3 domains/job، 5 pages/domain، 2 redirects، 2 MiB/page، 20s/page، concurrency 2، 60s total.
