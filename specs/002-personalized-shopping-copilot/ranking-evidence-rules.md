# Ranking and Evidence Rules

Pipeline `COPILOT-RANK-v0.1` (Phase 10 executable closure): `normalize → resolve_variant → hard_filters → total_cost → criteria → missing_policy → stable_tie → explain`.

## Executable categorical contract

Confirmed brief `comparison` stores intent PRACTICAL/ENJOYMENT/GIFT/HOUSEHOLD/UNKNOWN, STRICT (default) or explicitly
FLEXIBLE budget, up to six criteria `{field, expected, kind: HARD|PREFERENCE, scope: SELF|RECIPIENT|HOUSEHOLD}` and
explicit `prefer_lower_cost`. Gift uses RECIPIENT criteria only; household uses HOUSEHOLD; self uses SELF. Foreign-scope
criteria never contribute. Unstructured hard constraints stay unresolved; prose is never parsed into authoritative facts.
Explicit brief contradictions also keep comparisons unresolved. `no_alternatives` means no SUPPORTED non-intended
product; unresolved/incompatible alternatives may still be displayed honestly, never promoted to a supported option.
Category criteria: electronics capacity_gb/portable; home capacity_l/dishwasher_safe; sports size_eu/waterproof.
Equality is explicit (no guessed min/max). Product facts require same-variant SUPPORTED, fresh snapshot evidence;
conflicting values, stale, missing or unsupported attribution become UNKNOWN. Synthetic/captured claims retain their
labels and may exercise the same rules, but never become VERIFIED_SOURCE or current market recommendations.

Groups: INCOMPATIBLE if any known hard failure or strict-budget item/known total exceeds cap; UNRESOLVED if hard fact,
stock, budget or complete total is unknown; SUPPORTED otherwise. Unknown shipping/mandatory charges prevent confirmed
budget fit; FLEXIBLE above-budget is a disclosed tradeoff, not permission to increase a cap or a recommendation to spend.
With multiple merchant offers, a complete affordable offer supports a conditional purchase path. A complete expensive
offer does not prove every offer is over budget: a cheaper/unknown item-price offer with missing fees keeps cost unresolved.
Availability OUT_OF_STOCK excludes alternatives but the intended product remains visible. Unknown availability remains
unresolved. Up to four explicit same-category product variants; duplicate products are not extra alternatives.

Within a group, fewer unknown requested criteria first, then more supported preferences, then fewer failed preferences.
These categorical counts are coverage, not a numerical fit score. Missing facts cannot improve confidence or erase a
known failure. Lower complete total breaks a substantive tie only if prefer_lower_cost is explicitly confirmed;
unknown totals never win that tie. Final canonical variant ID only stabilizes presentation: equal substantive keys are
reported TIED, not a forced winner. If no SUPPORTED candidate exists, outcome is UNRESOLVED or NO_SUPPORTED_CHOICE.
Intended product stays identified regardless of its place. Every item exposes checks, evidence IDs, unknowns, tradeoffs,
coverage and would_change_if; explanations are labelled deterministic templates, not LLM text. One consequential
clarification asks about missing budget, recipient preference or the first unresolved requirement, never a questionnaire.

ChoiceSet stores immutable result items, relevant brief inputs, rule version, brief revision/generation and evidence snapshot references.
Read invalidates by brief revision/confirmation or source freshness; late publication rechecks owner/expiry/revision/epoch.
No evidence query crosses conversation ownership. Explicit demo loading seeds entities without network and labels all
three categories SYNTHETIC demonstration coverage. It does not change the confirmed brief or enable research.

- hard filters: strict budget، compatibility، required size/spec، fresh availability.
- total cost: known item + shipping + mandatory accessory + known fee؛ unknown component blocks `WITHIN_BUDGET_CONFIRMED`.
- No weighted or 0–100 scores; categorical comparisons use only admissible evidence and confirmed criteria.
- missing evidence is `UNKNOWN`, not zero/average; coverage shown separately.
- tie: constraint coverage، then lower known total cost only if confirmed preference، then canonical variant ID.

| Attribution | Rank use |
|---|---|
| `VERIFIED_SOURCE` | yes within freshness/identity scope |
| `USER_REPORTED` | personal criteria only، not product fact |
| `DETERMINISTIC` | yes |
| `ASSISTANT_INFERENCE` | explanation only until consequential confirmation |
| `UNKNOWN` | no contribution; lowers coverage |

Review/editorial/merchant rating types remain separate and retain source/sample/date/scale/limits. Every rank exposes rules، components، evidence IDs، missing fields، cost status، tradeoffs و `would_change_if`. Cases cover boundaries، unknown shipping، variant mismatch، gift context، conflicting sources، ties، stale offer and missing review.

## Phase 9.2 offer-view ordering (not product ranking)

- فقط offerهای یک `Variant` compatible در یک گروه قابل مقایسه‌اند؛ merchant SKU شناسهٔ cross-store نیست.
- ترتیب پیش‌فرض: `price_toman` معلوم صعودی، سپس seller normalized، observation time و UUID. قیمت نامعلوم بعد از قیمت معلوم است.
- same variant + normalized seller + same `price_toman` در view یکی می‌شود و `MERCHANT_PAGE_VERIFIED` بر `COMPARISON_OBSERVED` ترجیح نمایشی دارد؛ observation خام و اختلاف قیمت حذف نمی‌شود.
- `total_payable_toman` فقط وقتی item، shipping و mandatory charge معلوم‌اند معتبر است. unknown shipping/fee صفر نیست و «کمترین قیمت بین منابع بررسی‌شده» فقط item-price scope را توصیف می‌کند.
