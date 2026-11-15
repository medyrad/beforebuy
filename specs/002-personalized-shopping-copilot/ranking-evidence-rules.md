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

## Phase 9.2 offer-view ordering (not product ranking)

- فقط offerهای یک `Variant` compatible در یک گروه قابل مقایسه‌اند؛ merchant SKU شناسهٔ cross-store نیست.
- ترتیب پیش‌فرض: `price_toman` معلوم صعودی، سپس seller normalized، observation time و UUID. قیمت نامعلوم بعد از قیمت معلوم است.
- same variant + normalized seller + same `price_toman` در view یکی می‌شود و `MERCHANT_PAGE_VERIFIED` بر `COMPARISON_OBSERVED` ترجیح نمایشی دارد؛ observation خام و اختلاف قیمت حذف نمی‌شود.
- `total_payable_toman` فقط وقتی item، shipping و mandatory charge معلوم‌اند معتبر است. unknown shipping/fee صفر نیست و «کمترین قیمت بین منابع بررسی‌شده» فقط item-price scope را توصیف می‌کند.
