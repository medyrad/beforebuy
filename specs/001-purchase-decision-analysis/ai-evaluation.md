# M3 live-explanation evaluation

**Version:** `PDA-AI-EVAL-v1.2`  
**Status:** accounting correction specified; live run and human review remain pending.

## Independent synthetic dataset

Seven synthetic cases carry literal expected outcome and unknown IDs independent of model output:

| ID | Coverage | Expected outcome / unknowns |
|---|---|---|
| `EVAL-01` | essential replacement, within budget, target unknown | `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` / target capability |
| `EVAL-02` | literal Persian-digit price and zero budget | `BUDGET_MISMATCH` / none |
| `EVAL-03` | unknown budget | `PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN` / budget |
| `EVAL-04` | urgent replacement above budget | `BUDGET_MISMATCH` / none |
| `EVAL-05` | discretionary enjoyment with accepted tradeoff | `DISCRETIONARY_CHOICE_WITHIN_BUDGET` / target capability |
| `EVAL-06` | critical use and prompt-like product label | `PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET` / target capability |
| `EVAL-07` | contradictory current-state and essential-benefit answers | `INSUFFICIENT_CONTEXT` / justification + target capability |

The deterministic report is the baseline. AI cannot alter outcome, dimensions, unknowns, actions, arithmetic or primary
headline. The artifact stores only synthetic context, the deterministic baseline and rendered validated explanation—not
credentials, real-user input, raw provider transport, raw prompt or raw response.

## Separate evidence and fixed thresholds

- Code-enforced: schema/claim type, known and compatible IDs, exact outcome echo, exact unknown echo, lengths, duplicate
  references, deterministic budget state and explicit positive user-reported target-fit value + attribution.
- Human-reviewed: whether Persian prose is actually supported by referenced values, avoids unrelated/named alternatives
  and fabricated numbers, is readable/actionable, and adds usefulness. Valid IDs do not prove entailment.
- Structural validity, outcome equality and unknown preservation must pass in 100% of cases.
- Semantic support must pass every case. Until reviewed it is `null`, never zero or pass.
- Readability median >= 4/5 with no case < 3; actionability median >= 4/5; added usefulness median >= 3/5.
- Successful-call latency threshold remains 8s. For this tiny set the reported maximum is only the sample's upper end,
  not a production p95 estimate.
- Total experiment spend، structural validity، latency، human review و product cost target gateهای مستقل‌اند.
- `$0.0025/generation` آستانهٔ تاریخی قبل از انتخاب provider است. فقط 512 output token با تعرفهٔ `$30/M` تا
  `$0.01536` هزینه دارد؛ بنابراین مدل منتخب نمی‌تواند worst-case این target را برآورده کند. target به‌جای relax شدن
  `incompatible/pending product decision` ثبت می‌شود و overall pass تا تصمیم تازه null می‌ماند.
- total initial authorization برابر 100,000 تومان across restart/retry است و invoice provider را تضمین نمی‌کند.

No keyword blacklist or LLM-as-judge is treated as semantic validation. Threshold changes require a new dataset version
and rationale.

## Cost accounting

The shared estimator used by both adapter and runner covers UTF-8 bytes for instructions, input JSON and response schema,
then adds the larger of 15% or 256 input-token framing margin, the bounded 512-token output and all allowed attempts.
UTF-8 bytes are a conservative local token upper bound, not tokenizer-exact. Official OpenAI guidance says schemas and
request framing consume tokens and recommends the input-token endpoint for exact counts; this project does not add a
separate paid preflight call. Cached-input discounts are ignored.

هر attempt یک usage معلوم یا unknown allowance دارد. known usage جمع و هرگز clip نمی‌شود؛ unknown attempt به اندازهٔ
per-attempt reservation محافظه‌کارانه settle می‌شود. malformed output با usage معلوم نیز usage را حفظ می‌کند.
settlement idempotent است، observed overage visible می‌ماند و reserved underflow خطای integrity است. reservation
رهاشده با recovery صریح و محافظه‌کارانه settle می‌شود؛ این estimate invoice قطعی نیست.

deployment `AILiveBudgetWindow` در UTC روزانه rollover دارد. authorization اولیهٔ evaluation یک ledger پایدار مستقل
در تومان است و midnight/process restart آن را reset نمی‌کند. reserve هر دو scope در یک transaction کوتاه انجام می‌شود.
artifact قبل از call و پس از هر case با replace اتمیک checkpoint و در interruption با `status=incomplete` حفظ می‌شود.

Selected-provider pricing verified 2026-11-14 from AvalAI's model contract: `gpt-5.6-luna`, $5/M input,
$0.5/M cached input and $30/M output. Cached discounts are not assumed in reservation. The current IRT-per-UNIT rate
comes from the AvalAI User API immediately before evaluation and receives a 15% margin:
[model API](https://docs.avalai.ir/en/api-reference/models),
[User API](https://docs.avalai.ir/en/api-reference/user).

## Reproducible run and human review

The Phase 5.2 live command has no implicit spending budget and never enables direct OpenAI:

```bash
AVALAI_API_KEY=<set-locally> \
BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=1 \
BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN=100000 \
  python backend/manage.py evaluate_live_ai --artifact-dir artifacts/ai-evaluation
```

The command refuses a cap above 100,000 toman, fetches the current IRT-per-UNIT rate/credit before model calls, applies
a 15% conversion margin, and reserves all seven cases including retries. Estimates are not guaranteed invoice amounts.
It writes `artifacts/ai-evaluation/<run-id>.json`. Each case includes identifiers, baseline, rendered AI explanation,
attempts, tokens, latency, reserved/estimated cost، discrepancy، usage-accounting mode و چهار initially-null human field دارد. A reviewer fills
`semantic_support` (boolean), `readability`, `actionability`, `added_usefulness` (1..5), plus optional notes, then:

```bash
python backend/manage.py assess_ai_review artifacts/ai-evaluation/<run-id>.json
```

The assessor ties results to dataset/run/model/prompt/schema and returns `overall_pass: null` until every human field is
present. No total-success claim is allowed before human thresholds pass. The artifact directory is local evaluation
evidence; only synthetic artifacts may be retained or shared.
`T039` remains pending until both a real run and human review are complete.
