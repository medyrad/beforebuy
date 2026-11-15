# Free API onboarding review — 2026-11-16

Status: researched, NOT an implemented/eligible live connection. No account creation, purchase, authenticated
provider request or inference call. User requests a free router connection; existing confirmed users/backend are
in Iran. This review does not silently change that deployment decision.

## Primary-source comparison

| Candidate | Documented free offering | Eligibility / privacy | Selection |
|---|---|---|---|
| OpenRouter | Public documentation lists free variants with changing quotas; consult the linked official page and account limits before use. Chat variants use Chat Completions. `openrouter/free` chooses a model dynamically, so it is NOT selected for this fixed-contract application. | Reviewed terms do not establish affirmative service eligibility for Iran. Gateway retention and upstream endpoint policies differ; some free models permit training. No Persian quality measurement here. | Informational only; no selectable/runtime integration in this delivery. |
| Groq | Free tier exists with organization/model-dependent rate limits; paid Developer tier requires a payment method. | Reviewed services agreement/trust FAQ do not establish affirmative Iran eligibility. No account quota or Persian quality measurement. | Alternative only; no integration. |

Sources inspected:

- https://openrouter.ai/collections/free-models — quotas, failed-attempt accounting, free-vs-funded zero-price distinction and Chat Completions.
- https://openrouter.ai/terms — service/model-provider terms; absence of an explicit Iran statement is not approval or proof of prohibition.
- https://openrouter.ai/docs/guides/privacy/data-collection — default retention exceptions and upstream policy distinction.
- https://openrouter.ai/settings/keys — official sign-in/key creation route.
- https://console.groq.com/docs/rate-limits — free limits and organization-scoped quotas.
- https://console.groq.com/docs/billing-faqs — free versus paid upgrade.
- https://console.groq.com/docs/legal/services-agreement and https://trust.groq.com/faq — terms/data review.

## Exact next gate

Ask the candidate's support (user action; no message sent on their behalf):
“May an Iran-resident customer use your API for a shopping assistant with backend and end users in Iran?
Which exact free chat model and upstream endpoint permit that use? What retention/training rules apply to
prompts and images, and can routing be pinned without paid fallback?”

After an affirmative, attributable answer: pin one eligible model and protocol; revalidate output schema, stream,
image capabilities and usage fields; implement provider-bound encrypted credentials and the existing answer-plan
adapter; disable model/provider fallbacks; enforce free-only pricing, daily attempts including failures, and fail
closed for unavailable quota/model. Run stubbed tests before any separately permitted synthetic live evaluation.
Do not treat a gateway key or OpenAI-compatible URL as Responses compatibility or regional authorization.

The settings panel offers official external sign-in links and a pending explanation only. It deliberately does not
collect an unusable extra secret. The requested end-to-end free connection remains pending, not delivered.
