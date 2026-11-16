# Manual offer boundary — FR-094/095

POST `/api/v1/conversations/{id}/choices/manual-offers`, anonymous CSRF + active owner required.
Requires confirmed brief and integer `expected_revision`; 409 stale/unconfirmed, 404 foreign/expired,
422 invalid input, 201 created, 200 identical replay. No network, credential, retention extension or technical claim.

JSON: `expected_revision`, optional `variant_id`, `same_variant_confirmed` boolean, `identity` object,
`seller`, `source_url`, `amount` (digit string or null), `currency` (`IRR|TOMAN`), `shipping_toman`,
`mandatory_toman` (digit strings or null), `availability` (`IN_STOCK|OUT_OF_STOCK|UNKNOWN|PREORDER`),
`observed_at` (timezone-aware ISO8601, not future). Reject extra fields. Max100 manual offers per conversation.

Identity: required bounded `brand`, `model_name`, `model_code`, `category` (`electronics|home|sports`),
`capacity`, `size`, `year`, `region`, `warranty` (explicit `UNKNOWN` allowed),
`condition` (`NEW|USED|REFURBISHED|UNKNOWN`), `bundle` (`YES|NO|UNKNOWN`).
New submissions create a separate user-entered variant, never auto-merge with extracted identities.
Existing variant must belong to this conversation's USER-ENTRY-v1 snapshots, with identical descriptor and
explicit same-variant confirmation. Unknown descriptors stay visible; comparisons are conditional on user's identity claim.

Amounts accept Persian/Arabic/ASCII digits, optional standard grouping separators; no negatives/fractions/scientific
notation, max10^12 toman. IRR must divide exactly by10; no rounding or guessed currency. Missing price/fees null.
HTTPS source URL only, no credentials/control characters/backslashes, IP literal/nonpublic-style hostname,
custom port or fragment; server never fetches manual URLs. Browser shows external-source link, no auto-navigation.

Response: `{variant_id, offer_id, attribution: USER_REPORTED}`. Existing candidates GET also supplies `identity`,
original amount/unit, server `entered_at`, claimed `observed_at`, stale/stock and full-cost fields. Identical merchant
observations display once; distinct conflicting price/stock/cost observations remain labelled. Freshness6h from claimed
observation, not entry. Manual provenance is permanent even when stale; it never becomes VERIFIED_SOURCE.
No `EvidenceClaim` is created; ranking excludes USER_REPORTED. Price-only table is not a recommendation.
