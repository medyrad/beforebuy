# Free API onboarding review — 2026-11-16

## Current bounded OpenRouter review (T098, supersedes the general shortlist below)

Decision: no runtime route selected. Exactly two free text-chat candidates reviewed; no third model/provider
evaluation, authenticated request, account creation, inference, privacy-setting change or credit purchase.
This is an unresolved suitability gate, **not a finding that Iranian use is prohibited**. A key alone does not
resolve the gate. T096 remains pending; do not expose an OpenRouter key form that cannot be used.

| Exact current route | Public endpoint evidence | Upstream contract and unresolved question |
|---|---|---|
| `nvidia/nemotron-3.5-lightning:free`, endpoint tag `nvidia/nvfp4` | Public endpoint API reports text→text, prompt/completion `0` USD/token, 1,000,000 context, 65,536 max completion. `response_format`/`structured_outputs` absent from supported parameters: compatibility with the current structured answer contract is not established. | Model page requires NVIDIA trial terms and excludes confidential/personal data; logging for security/improvement disclosed. Trial §15.4 requires export/sanctions compliance. It does not itself determine whether this Iranian app/account qualifies; no blanket ban inferred. |
| `baidu/ernie-5.5-flash-preview:free`, endpoint tag `baidu` | Public endpoint API reports text→text, prompt/completion `0` USD/token, 1,024,000 context, 921,600 max completion and `response_format`/`structured_outputs`. These are capability claims, not measured schema adherence or Persian quality. | Linked Baidu international terms §§2.3/3.2 make regional availability conditional; §§3A.3–4 permit storage/improvement/cross-border processing and require end-user consent. OpenRouter's provider table says prompts retained. No affirmative route/account eligibility for Iran or bounded retention duration established. |

Public evidence (review date above; tariffs/capacity can change):

- [NVIDIA exact endpoints](https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-lightning:free/endpoints)
  and [model policy notice](https://openrouter.ai/nvidia/nemotron-3.5-lightning:free).
- [NVIDIA API Trial terms](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf).
- [Baidu exact endpoints](https://openrouter.ai/api/v1/models/baidu/ernie-5.5-flash-preview:free/endpoints)
  and [hosting-provider page](https://openrouter.ai/provider/baidu), linking
  [Baidu international product terms](https://intl.cloud.baidu.com/en/doc/Agreements/s/bmesahnjh-intl-en).
- [OpenRouter service terms](https://openrouter.ai/terms): eligibility/compliance and upstream terms are separate;
  model geography restrictions cannot be bypassed. Reviewed general terms do not establish this route's Iran
  eligibility. Generic credit-purchase wording is not used to override the specific free-variant documentation.
- [Free collection FAQ](https://openrouter.ai/collections/free-models): `:free` needs no credit purchase;
  current published caps are 20/minute, 50/day for unfunded accounts, failed attempts included. These are
  service-level claims, not a checked account allowance or guaranteed capacity. No purchase is authorized.
- [API FAQ](https://openrouter.ai/docs/faq): fixed Chat Completions endpoint
  `https://openrouter.ai/api/v1/chat/completions`, SSE with `stream:true`. Account privacy restrictions can reject
  an upstream route. OpenRouter metadata logging is distinct from upstream content retention.
- [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection): pin an exact `only` endpoint,
  `allow_fallbacks:false`, `require_parameters:true`; price filters are available but are not invoice proof.
  [Provider privacy table](https://openrouter.ai/providers) supplements, not replaces, upstream terms.

### Precise unblock request (not sent on the user's behalf)

Ask OpenRouter support (`support@openrouter.ai`, official FAQ contact): can an Iran-resident account with
Iran-hosted backend/end users use the exact Baidu free endpoint above without funding? Which upstream regional
terms apply through OpenRouter, what retention/deletion/training terms apply, and does any charge other than
prompt/completion apply when tools/plugins/fallbacks are absent? Ask for an attributable answer, not a generic
model-list link. NVIDIA additionally needs clarification of the trial/export applicability and structured-output
support. The attempted separate Qianfan-specific international documentation URL timed out; the terms linked
directly from OpenRouter were accessible and reviewed. Missing documentation is not evidence of prohibition.

Only after eligibility and informed privacy consent are established: implement the existing T096 boundary with
encrypted separate key, local “آزمایش رایگان” action, a durable **10 total generation-attempt** allowance (including
validation/retries), paid authorization false and monetary cap zero, explicit token/time limits and current
pricing verification for all applicable charges. Unknown/nonzero charges fail closed. Never use `openrouter/free`,
strip `:free`, enable fallback or change account privacy automatically. Preserve usage/provider/model/returned
cost separately from documented zero pricing. These controls are requirements, **not implemented claims**.

Live results: 0 attempts, no usage or invoice evidence; Persian/context/stream/stop/error quality unmeasured.
No OpenRouter credential should be entered into OpenAI/GapGPT fields. No local activation steps exist yet;
after the eligibility gate, T096 must add the dedicated encrypted UI before the user supplies that key there.

## Historical general review (not additional candidates for T098)

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
