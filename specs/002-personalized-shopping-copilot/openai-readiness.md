# Phase 11 OpenAI readiness

Status: implementation/stub verification only; **live activation blocked**. No provider calls are authorized.
Confirmed users and deployment are in Iran. Saving a key is not eligibility, account validation, or spending consent.

## Primary-source review

Reviewed 2026-11-15 using official OpenAI documentation:

- [gpt-6-luna model](https://developers.openai.com/api/docs/models/gpt-6-luna): exact catalog ID `gpt-6-luna`;
  Responses, streaming, structured outputs and image input documented. Account availability is unverified.
- [Pricing](https://developers.openai.com/api/docs/pricing): standard short-context input USD 0.10/M tokens,
  output USD 0.50/M, cached input USD 0.01/M; 12-hour cache write USD 0.25/M. These are documented tariffs,
  not a measured invoice. The bounded adapter conservatively uses the higher input rate; no long-context or
  regional processing surcharge configuration is enabled. Revalidate before any future live authorization.
- [Responses streaming](https://developers.openai.com/api/docs/guides/streaming-responses): SDK event types are
  parsed, not treated as Chat Completions chunks. SDK retries are disabled; application attempts are capped at two.
- [Data controls](https://developers.openai.com/api/docs/guides/your-data): `store=false` is not zero retention;
  abuse monitoring and provider-side cache retention are separate concerns.
- [Supported countries](https://developers.openai.com/api/docs/supported-countries): Iran is not supported.
  The eligibility gate rejects independently of a stored key or environment/browser checkbox.

## Contract and scope

- `discover_models(account_ids, saved_model=...)` intersects account IDs with explicit capability/pricing metadata.
  With no account evidence it returns `DOCUMENTATION_UNVERIFIED`/`ACCOUNT_UNVERIFIED`; a missing saved model is
  `UNAVAILABLE`, never silently substituted. No model-list HTTP request occurs in this phase.
- Phase 11.1 replaces the clarification-only schema with a narrow answer-plan contract. It selects a controlled lead
  and typed blocks referencing only the assembled current candidates/criteria/evidence. Persian factual wording is
  deterministic after value/attribution/freshness/variant validation; model prose is not evidence. Safe leads and
  validated blocks remain provisional until final publication.
- Responses uses `store=false`, standard service tier, a 256-output-token ceiling, bounded text/image input,
  per-attempt timeout and transient-only bounded retries. Cancellation/invalid output never publishes a final answer.
- OpenAI SDK transport is tested with HTTP stubs. No AvalAI fallback or configurable alternate base URL is allowed.
- Existing `LiveBudgetLedger`/`AIInvocation` owns reservations and settlement, including missing usage. Purchase
  money remains whole toman; AI runtime accounting uses integer micro-USD. Estimates are not invoice guarantees.
- Operation/session/daily caps default to zero. Missing finite configuration fails closed. Credential creation,
  replacement, model selection and memory operations never authorize spending or make provider calls.
- The installed SDK 3.49.0 documents `client.models.list()` as `GET /models`; the new seam is HTTP-stub tested only.
  Explicit refresh remains region/validated-credential gated and returned IDs are intersected with this catalog.

## Remaining gates

Persistent session accounting and credential-snapshot/publication guards are implemented and regression tested.
The worker-to-Responses-to-final-message path is tested with an injected transport and a test-only eligibility stub;
the production gate remains unconditional for the confirmed Iran deployment. Actual regional eligibility, account model access,
credential validation, product-reviewed retention and separately authorized live spending remain future gates even
after stub tests pass. Feature 001 T039, feature 002 T047/T050 and full Milestone E are not completed here.

Final backend/browser counts and any remaining verification limitations are recorded in `docs/handoff.md`;
test-only fabricated validation states are not evidence that a real credential or account was validated.
