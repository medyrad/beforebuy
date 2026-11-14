# Ranking and Evidence Rules

Pipeline `COPILOT-RANK-v0.1`: `normalize → resolve_variant → hard_filters → total_cost → criteria → missing_policy → stable_tie → explain`.

- hard filters: strict budget، compatibility، required size/spec، fresh availability.
- total cost: known item + shipping + mandatory accessory + known fee؛ unknown component blocks `WITHIN_BUDGET_CONFIRMED`.
- scores use only normalized verified/user-confirmed values and versioned weights؛ LLM prose never numeric input.
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
