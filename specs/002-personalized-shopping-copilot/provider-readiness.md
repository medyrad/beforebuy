# Phase 12 provider readiness

Status: selected adapter implementation and stub verification are authorized. Live validation/generation is not yet
authorized. This file records first-party documentation checked on 2026-11-15; provider claims are not workspace measurements.

## Shortlist

| Criterion | GapGPT | AvalAI |
|---|---|---|
| Iran application eligibility | Iranian service, direct access and commercial API use documented | Iranian API service and Iran endpoints documented |
| Selected exact model | `gapgpt-deepseek-v4.1-flash`, described as GapGPT-hosted/processed in Iran | no model selected; upstream eligibility varies by routed model |
| Protocol | fixed `https://api.gapgpt.app/v1`, Chat Completions, streaming documented | fixed AvalAI endpoints; Responses and Chat Completions documented |
| Structured/tool output | not documented for the exact selected model | structured output documented for some models; must revalidate per model |
| Persian suitability | provider markets Persian access; not measured here | not measured here |
| Privacy/retention | provider states Iran processing/no export for selected model; general terms retain account/content/log data under applicable law; exact API retention duration unresolved | provider policy/data path and upstream retention must be revalidated per routed model |
| Tariff | USD 0.15/M input, 0.015/M cached input, 0.60/M output | exact tariff depends on selected routed model/service tier |
| Account/top-up | free/start-credit claims exist, but API availability/minimum top-up for this model is unverified | base balance/credit/account tier requirements documented; no purchase is authorized |

## Selection

GapGPT is selected because the exact model is explicitly described as locally hosted in Iran and the documented
Chat Completions streaming path is the smallest change compatible with the existing worker/SSE/context/ledger. The
adapter does not use arbitrary base URLs and does not claim Responses, JSON Schema or tool support. It asks for a
bounded JSON answer plan as plain text, validates every field, and renders evidence-backed facts server-side.

AvalAI is the fallback recommendation only. It is not configured or selected automatically because listing a routed
model does not prove upstream authorization or its data path for Iranian users.

## Live gate

Before any real call, all of the following are required:

1. A GapGPT key entered only through the local encrypted settings UI; never chat/Git/frontend/env examples.
2. Explicit validation action and successful provider response for the exact selected model.
3. Product-lead spending authorization for Phase 12, a dated USD→toman rate, conservative margin and hard total cap
   including retries. Historical AvalAI allowances are not reused.
4. Synthetic scenarios and human review covering relevance, repeated questions, context, unsupported claims,
   stop/retry/error, changed budget, gift/recipient, enjoyment, insufficient technical evidence and current-price
   requests with research OFFLINE.

Until then actual calls, retries, provider tokens, latency and cost are all zero/unmeasured and connection state must
remain stored-unvalidated or blocked—not connected/live-verified.

### Proposed Phase 12 evaluation envelope (not authorized)

The proposed hard total is **50,000 toman**, shared by validation, scenarios and retries under authorization ID
`phase12-gapgpt-live`. It is a proposal, not a reusable allowance. Before activation the lead must approve that exact
amount and record a dated USD→toman rate; the configured 15% conversion margin is conservative accounting, not an
invoice guarantee. Per-operation/session/deployment micro-USD caps must also be positive. The durable authorization
ledger locks reserved plus estimated spend before transport and missing usage is charged at the reservation bound.

After written approval only: keep research `OFFLINE`, create/mount the existing copilot master keyring, enter the
GapGPT key in the settings UI, configure the newly approved rate/caps, and set `COPILOT_PHASE12_SPENDING_AUTHORIZED=1`.
Then press «بررسی صریح مدل‌های حساب» once. Because GapGPT documents no free model-list/auth probe, that explicit action
performs one bounded, ledger-accounted Chat Completions generation against the exact selected model. Only its validated
response changes the matching credential revision to `VALIDATED`; save/read/settings remain zero-call. Do not flip the
database state manually. A changed key returns to `STORED_UNVALIDATED` and cancels dependent work.
