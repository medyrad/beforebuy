# Source Feasibility Register

**Review date:** 2026-11-15  
**Phase 9 live probes:** 7 HTTP GET، zero retry، zero provider/model call؛ `--noproxy '*'`، redirects ≤2، 2 MiB cap، 20s timeout، user-agent معرفی‌شده. Search/index evidence با direct workspace probe و extraction جداست.

## Readiness vocabulary

`SYNTHETIC_FIXTURE` ≠ `CAPTURED_REAL_FIXTURE` ≠ `LIVE_PROBE` ≠ `REPEATABLE_LIVE_EXTRACTION` ≠ `ENABLED`.
HTTP 200 extraction نیست؛ extraction permission/license نیست؛ robots جامع نیست؛ timeout منع دائمی نیست. default runtime `OFFLINE` است و live failure به fixture fallback نمی‌کند.

## Register

| Domain / exact paths | Role/category | Policy evidence (URL, observed) | Direct observation | Identity / extracted fields | Retention/display/rate | Decision |
|---|---|---|---|---|---|---|
| `www.apple.com` `/iphone-*/specs/` | manufacturer/electronics | [robots](https://www.apple.com/robots.txt)؛ [Website Terms](https://www.apple.com/legal/internet-services/terms/site.html)، reviewed 2026-11-15؛ terms automated page-scrape/robot access را منع می‌کند | Phase 7 captured page existed؛ Phase 9 product request deliberately zero after terms review | prior model/capacity/dimensions/display observation؛ not repeated | no retention/display approval for this service | `DISABLED`؛ captured fixture may remain historical only، not live allowlist |
| `www.philips.com` exact `/c-p/EP5934_10R1/.../overview`؛ no redirects | manufacturer/appliance | [robots](https://www.philips.com/robots.txt) 200/254 B؛ [Terms of use](https://www.philips.com/a-w/terms-of-use.html?locale_code=en_aa)، reviewed 2026-11-15 | product 200، `text/html;charset=utf-8`، 33,782 B، 0 redirect، 0.330s؛ JSON-LD extraction successful | exact `EP5934/10R1`؛ name، SKU، MPN، brand؛ no offer/price. Web text also exposes specs but fixture intentionally retains only JSON-LD identity | raw ≤24h، minimal field values/citation only، freshness 30d، pace ≥1s. Terms do not explicitly authorize this product-research integration or redistribution | `CAPTURED_REAL_FIXTURE` + `LIVE_PROBE`; live `DISABLED` pending Philips clarification/permission |
| `www.technolife.com` exact `/product-99474/...`؛ no redirects | merchant/electronics | [robots](https://www.technolife.com/robots.txt) 200/589 B؛ [قوانین](https://www.technolife.com/staticpage/page-14/%D9%82%D9%88%D8%A7%D9%86%DB%8C%D9%86%20%D9%88%20%D9%85%D9%82%D8%B1%D8%A7%D8%AA) 200/134,718 B، reviewed 2026-11-15 | product 200، `text/html; charset=utf-8`، 147,320 B، 0 redirect، 0.485s؛ JSON-LD + explicit availability extraction successful | Samsung Galaxy A56 5G 256GB/8GB؛ SKU/MPN `99474`، brand، `OUT_OF_STOCK`; no price/offer/shipping in captured page، so total payable unknown | raw ≤24h، offer freshness ≤6h if later enabled، pace ≥2s، citation + minimal excerpt. Terms address customer registration/sale but not automated extraction, retention or republication | `CAPTURED_REAL_FIXTURE` + `LIVE_PROBE`; live `DISABLED` pending written clarification |
| `torob.com` `/pages/terms/`; product paths not approved | comparison/Iranian offers | [robots](https://torob.com/robots.txt) 200/110 B؛ [terms](https://torob.com/pages/terms/) 200/11,234 B، reviewed 2026-11-15 | 2 requests؛ no product request/extraction. Terms say Torob aggregates merchant information but do not grant this service extraction/display rights | no exact product/variant/offer | no retention/display license found؛ would require exact product policy، source merchant attribution and ≤2s pace | `LIVE_PROBE` policy only؛ `DISABLED` pending clarification and exact offer extraction |
| `digikala.com` | merchant/Iranian offers | Phase 7 robots/root timed out at 12s؛ no accessible terms conclusion | Phase 9 requests zero؛ repeated retries intentionally avoided | none | unresolved | `DISABLED/UNASSESSED`; timeout is not permanent unavailability |
| `nike.com` product `/t/` | manufacturer/sports-fashion | prior robots/path observation plus public anti-bot posture; exact product terms permission not established | Phase 9 product requests zero | search/index result exposes style/size examples but is not workspace extraction | unresolved | `DISABLED`; no sports fixture/readiness |
| `adidas.com` | manufacturer/sports-fashion | [Platform terms](https://adidasapp.adidas.com/legal/confirmed/en-US/terms.html)، reviewed 2026-11-15؛ robot/spider/scraper access without written permission prohibited | requests zero after terms review | none | written permission required | `DISABLED` |
| `decathlon.com` | merchant/manufacturer sports-fashion | [Terms of service](https://www.decathlon.com/policies/terms-of-service)، reviewed 2026-11-15؛ automated access/monitor/copy prohibited without written consent | requests zero after terms review | none | prior written consent required | `DISABLED` |

## Coverage and allowlist decision

- **Enabled live source integration:** none. Essential permission/retention/display terms remain unresolved even where HTTP and extraction succeeded. Runtime live mode therefore returns explicit `NO_SUPPORTED_SOURCES` and performs zero outbound calls; fixtures are never fallback.
- **Captured real fixture verified:** Philips appliance identity and Technolife electronics merchant identity/out-of-stock state. Both are minimal, checksummed and labelled historical/non-current in `backend/tests/fixtures/research/manifest.json`.
- **Iranian offer feasibility:** Technolife page was directly reachable/extractable but contained no current price and was out of stock. Torob policy pages were reachable but exact offer extraction was not performed. No cheapest-in-Iran or current availability claim is supported.
- **Sports/fashion:** blocked. Nike permission is unresolved and adidas/Decathlon terms disallow the required automated access without permission. `T018` and `T019` remain incomplete for sports coverage.
- **Required clarification:** ask Philips and Technolife whether low-volume automated retrieval for attributed comparison is permitted, which fields/excerpts may be displayed, maximum retention, required attribution/contact and rate policy. Ask Torob whether a documented public feed/API or licensed terms exist for offer reuse.

## Approved runtime policy

Explicit user trigger only؛ 3 domain/job، 5 content page/domain، 2 redirect/request، 20 HTTP request total، 2 MiB decoded/page، 20s/request، 60s/job، outbound concurrency 2/application process، one active job/guest، per-domain pace at least 1s (stricter source policy wins). Redirect/retry/policy requests consume budget. `Retry-After` may be honored only inside remaining deadline; implementation has no unbounded retry. Process-local semaphore is not deployment-global.

Raw response cache expires at creation+24h without sliding read. Offer freshness is source-specific and never inferred from cache presence. Normalized private evidence cannot outlive its owning conversation; backup erasure remains bounded by backup lifecycle.
