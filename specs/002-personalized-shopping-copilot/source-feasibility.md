# Source Feasibility Register

**Review date:** 2026-11-15  
**Phase 9 live probes:** 7 HTTP GET، zero retry، zero provider/model call؛ `--noproxy '*'`، redirects ≤2، 2 MiB cap، 20s timeout، user-agent معرفی‌شده. Search/index evidence با direct workspace probe و extraction جداست.  
**Phase 9.2 policy/feasibility probes before pilot:** 19 controlled outbound requests including redirects، zero retry/provider call. Browser-assisted discovery is reported separately because its internal request count is not observable from the workspace.

## Readiness vocabulary

`SYNTHETIC_FIXTURE` ≠ `CAPTURED_REAL_FIXTURE` ≠ `LIVE_PROBE` ≠ `REPEATABLE_LIVE_EXTRACTION` ≠ `ENABLED`.
HTTP 200 extraction نیست؛ extraction permission/license نیست؛ robots جامع نیست؛ timeout منع دائمی نیست. default runtime `OFFLINE` است و live failure به fixture fallback نمی‌کند.

## Register

| Domain / exact paths | Role/category | Policy evidence (URL, observed) | Direct observation | Identity / extracted fields | Retention/display/rate | Decision |
|---|---|---|---|---|---|---|
| `www.apple.com` `/iphone-*/specs/` | manufacturer/electronics | [robots](https://www.apple.com/robots.txt)؛ [Website Terms](https://www.apple.com/legal/internet-services/terms/site.html)، reviewed 2026-11-15؛ terms automated page-scrape/robot access را منع می‌کند | Phase 7 captured page existed؛ Phase 9 product request deliberately zero after terms review | prior model/capacity/dimensions/display observation؛ not repeated | no retention/display approval for this service | `DISABLED`؛ captured fixture may remain historical only، not live allowlist |
| `www.philips.com` exact `/c-p/EP5934_10R1/.../overview`؛ no redirects | manufacturer/appliance | [robots](https://www.philips.com/robots.txt) 200/254 B؛ [Terms of use](https://www.philips.com/a-w/terms-of-use.html?locale_code=en_aa)، reviewed 2026-11-15 | product 200، `text/html;charset=utf-8`، 33,782 B، 0 redirect، 0.330s؛ JSON-LD extraction successful | exact `EP5934/10R1`؛ name، SKU، MPN، brand؛ no offer/price. Web text also exposes specs but fixture intentionally retains only JSON-LD identity | raw ≤24h، minimal field values/citation only، freshness 30d، pace ≥1s. Terms do not explicitly authorize this product-research integration or redistribution | `CAPTURED_REAL_FIXTURE` + `LIVE_PROBE`; live `DISABLED` pending Philips clarification/permission |
| `torob.com` exact `/p/<uuid>/<slug?>` only; `/search/` excluded | comparison/Iranian offers | [robots](https://torob.com/robots.txt) disallows `/search/` but not `/p/`؛ [terms](https://torob.com/pages/terms/) says Torob aggregates merchant data and redirects purchase to merchants، reviewed 2026-11-15. No relevant explicit automated-extraction prohibition or reuse permission found | exact Samsung Q60D product returned 200 after one canonical redirect؛ embedded `__NEXT_DATA__` contains product identity and multiple seller offers | comparison-observed seller، item price explicitly labelled toman، availability، merchant redirect URL and some postage fields | raw ≤24h، evidence conversation-owned، offer freshness 6h، pace ≥2s، exact URLs only، factual fields + Torob/merchant attribution | `ENABLED_NARROW_PILOT`; reasoned low-volume factual observation، not blanket permission or market coverage؛ upstream merchant terms/independent verification remain unresolved |
| `digikala.com` exact `/product/dkp-*` only | merchant/Iranian offers | [robots](https://www.digikala.com/robots.txt) disallows query/search and `dkpi-*` paths but not observed `dkp-*`؛ [terms](https://www.digikala.com/page/terms/) reviewed 2026-11-15. Footer describes source-attributed non-commercial content use; no consumer-offer API was identified | exact product HTML returned only routing shell؛ guessed product API endpoint returned 404. No CAPTCHA bypass/retry | no trustworthy product/offer extraction | no live policy until a stable documented/public representation is demonstrated | `DISABLED_TECHNICAL_EXTRACTION_FAILURE`; not classified as legal prohibition and not permanent unavailability |
| `www.technolife.com` exact `/product-*` | direct merchant/electronics + appliance | [robots](https://www.technolife.com/robots.txt) and [terms](https://www.technolife.com/staticpage/page-14/%D9%82%D9%88%D8%A7%D9%86%DB%8C%D9%86%20%D9%88%20%D9%85%D9%82%D8%B1%D8%B1%D8%A7%D8%AA)، reviewed 2026-11-15؛ no relevant explicit automated-access rule found in inspected material | exact Nokia 105 and Philips NA230 pages accessible. Generic JSON-LD can conflict with visible toman unit (`IRR` code with same numeric displayed as toman), so generic normalization MUST fail closed; source-specific adapter required | product identity، direct merchant/seller، explicit visible toman price، availability and product URL when layout is validated | same narrow retention/attribution/freshness/pace controls; shipping unknown unless explicit | `ENABLED_NARROW_PILOT` only through conflict-detecting source adapter; absence of explicit rule is not permission |
| `bkalaa.com` exact `/product/*` | direct merchant/appliance | [robots](https://bkalaa.com/robots.txt)، reviewed 2026-11-15؛ admin/cart/log paths disallowed، product path not disallowed؛ no relevant explicit automated-access/reuse rule found in inspected public pages | `/product/na230/` 200؛ JSON-LD Offer `24466434 IRT` and InStock | exact product، direct merchant، explicit IRT price، availability؛ shipping/mandatory charges unknown | exact URL، raw ≤24h، freshness 6h، pace ≥2s، attribution | `ENABLED_NARROW_PILOT`; unresolved reuse/retention terms recorded، no blanket permission claim |
| `takkalaban.com` exact `/product/*` | direct merchant/appliance | [robots](https://takkalaban.com/robots.txt)، reviewed 2026-11-15؛ cart/search/filter excluded، product path not disallowed؛ no relevant explicit automated-access/reuse rule found | `/product/philips-na230/` 200؛ JSON-LD Offer `239900000 IRR` and InStock | exact product، direct merchant، explicit IRR converted by 10:1 rule، availability؛ shipping/mandatory charges unknown | exact URL، raw ≤24h، freshness 6h، pace ≥2s، attribution | `ENABLED_NARROW_PILOT`; unresolved reuse/retention terms recorded، no blanket permission claim |
| `nike.com` product `/t/` | manufacturer/sports-fashion | prior robots/path observation plus public anti-bot posture; exact product terms permission not established | Phase 9 product requests zero | search/index result exposes style/size examples but is not workspace extraction | unresolved | `DISABLED`; no sports fixture/readiness |
| `adidas.com` | manufacturer/sports-fashion | [Platform terms](https://adidasapp.adidas.com/legal/confirmed/en-US/terms.html)، reviewed 2026-11-15؛ robot/spider/scraper access without written permission prohibited | requests zero after terms review | none | written permission required | `DISABLED` |
| `decathlon.com` | merchant/manufacturer sports-fashion | [Terms of service](https://www.decathlon.com/policies/terms-of-service)، reviewed 2026-11-15؛ automated access/monitor/copy prohibited without written consent | requests zero after terms review | none | prior written consent required | `DISABLED` |

## Coverage and allowlist decision

- **Enabled live source integration after Phase 9.2 implementation:** only the narrow exact-product policies above، installed explicitly by an operator command and still gated by `BEFOREBUY_RESEARCH_MODE=LIVE`. Default runtime remains `OFFLINE`; fixtures are never fallback. Apple/adidas/Decathlon and every excluded/search/account path remain disabled.
- **Captured real fixture verified:** Philips appliance identity and Technolife electronics merchant identity/out-of-stock state. Both are minimal, checksummed and labelled historical/non-current in `backend/tests/fixtures/research/manifest.json`.
- **Iranian offer feasibility:** Technolife page was directly reachable/extractable but contained no current price and was out of stock. Torob policy pages were reachable but exact offer extraction was not performed. No cheapest-in-Iran or current availability claim is supported.
- **Sports/fashion:** blocked. Nike permission is unresolved and adidas/Decathlon terms disallow the required automated access without permission. `T018` and `T019` remain incomplete for sports coverage.
- **Required clarification:** ask Philips and Technolife whether low-volume automated retrieval for attributed comparison is permitted, which fields/excerpts may be displayed, maximum retention, required attribution/contact and rate policy. Ask Torob whether a documented public feed/API or licensed terms exist for offer reuse.

## Approved runtime policy

Explicit user trigger only؛ 3 domain/job، 5 content page/domain، 2 redirect/request، 20 HTTP request total، 2 MiB decoded/page، 20s/request، 60s/job، outbound concurrency 2/application process، one active job/guest، per-domain pace at least 1s (stricter source policy wins). Redirect/retry/policy requests consume budget. `Retry-After` may be honored only inside remaining deadline; implementation has no unbounded retry. Process-local semaphore is not deployment-global.

Raw response cache expires at creation+24h without sliding read. Offer freshness is source-specific and never inferred from cache presence. Normalized private evidence cannot outlive its owning conversation; backup erasure remains bounded by backup lifecycle.

## Phase 9.1 controlled-pipeline evidence (2026-11-15)

- Public-source enablement remains exactly empty؛ no public request was made in Phase 9.1.
- A controlled `products.example` policy exists only inside PostgreSQL tests. DNS returns a documentation-safe public
  address and a test-only connector sends the socket to a loopback `ThreadingHTTPServer`؛ production validation has no
  localhost flag or private-address exception.
- The real start API requires an exact product URL، then executes policy → bounded fetch → JSON-LD extraction → variant
  identity → timed offer/claims → atomic snapshot/events. The test records one request، positive wire/decoded bytes،
  exact Host/path، one offer and attributed claims.
- Disabled policies produce `BLOCKED/SOURCE_DISABLED` with zero outbound connection. This verifies plumbing/accounting
  only؛ it does not establish public permission، freshness، Persian catalog coverage or uncontrolled extraction quality.
- Provider calls remain zero. `T013`, `T018` and `T019` remain partial for the recorded permission/sports blockers.

## Phase 9.2 five-product live attempt (2026-11-15)

The actual NGINX/API pipeline attempted five exact products across appliances، electronics and tools. Jobs and evidence
are retained in the local development database; no fixture fallback occurred:

| Product / targets | UTC observation window | Pipeline result | requests / redirects | comparable live offers |
|---|---|---|---:|---:|
| Philips NA230 — Technolife، Bkalaa، Takkalaban | `05:29:16–05:29:37` | initial Technolife path policy rejected؛ Bkalaa `DNS_ERROR`؛ Takkalaban `TRANSPORT_ERROR` | 2 / 0 | 0 |
| Samsung Q60D 55 — Torob | `05:29:38–05:29:58` | `TRANSPORT_ERROR` | 1 / 0 | 0 |
| Pakshoma TFB-95401 — Torob | `05:29:59–05:30:19` | `TRANSPORT_ERROR` | 1 / 0 | 0 |
| Tokyo 52cc chainsaw — Torob | `05:30:20–05:30:40` | `TRANSPORT_ERROR` | 1 / 0 | 0 |
| Nokia 105 2024 — Technolife | `05:30:41` | initial exact-ID path policy rejected before network | 0 / 0 | 0 |

The Technolife policy was then narrowed to the two reviewed exact product IDs; a post-fix NA230 request at
`05:34:49–05:35:10` reached transport and returned `TRANSPORT_ERROR`. A browser-driven Torob run at
`05:42:43–05:43:03` reproduced `TRANSPORT_ERROR` in the actual UI. Direct pinned connections time out from this
workspace and Bkalaa DNS failed; using a proxy or weakening SSRF/IP pinning was rejected. These are current environment
access failures، not proof of permanent source unavailability.

Controlled Phase 9.2 outbound accounting is **29/100**: 19 policy/feasibility requests، 7 persisted live-pipeline
requests، and 3 bounded transport diagnostics. Browser-assisted documentation lookups are reported separately because
their internal request count is not measurable. No retry، provider/model call، account، purchase or bypass occurred.

Before the network regression، minimal direct probes/existing captured bodies demonstrated deterministic adapter output:
Torob Q60D six comparison observations (`109,600,000` to `115,890,000` toman)، Bkalaa NA230 `24,466,434 IRT`
(same toman amount)، and Takkalaban NA230 `239,900,000 IRR = 23,990,000 toman`. These are feasibility/captured
observations، not successful live-pipeline evidence and not a current invoice/market-wide price claim. Therefore the
three-live-merchant target and successful-source repeat remain unmet; `T066` stays partial.
