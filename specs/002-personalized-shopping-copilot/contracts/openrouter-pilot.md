# T096 synthetic OpenRouter pilot

Existing credential GET/PUT/DELETE accepts `provider: openrouter` with the same CSRF/owner/CAS/encryption rules.
Opening settings and saving/removing a key make zero provider requests. Settings response adds `openrouter` gates:
technical support, service eligibility, route eligibility, data consent, remaining deployment-wide attempts,
and actual credential validation state. No operator can set credential VALIDATED via settings.

POST `/api/v1/copilot/models/refresh` while OpenRouter is selected requires `synthetic_consent:true`.
It requires explicit consent, checks eligibility and zero-paid configuration, decrypts this provider's key only,
checks current exact endpoint metadata and makes one bounded synthetic generation (one of ten total attempts).
On validated output, returned zero cost/usage and unchanged settings/key revision it records consent, marks that credential validated and creates a fresh
temporary `openrouter_pilot` conversation; response includes existing catalog plus `conversation_id`.
No previous conversation/profile/image is submitted. Failure returns the existing error envelope and no conversation.
Repeated explicit actions consume attempts, never reset the global allowance. No automatic retry.

Pilot messages require selected OpenRouter, consent and validated current credential, no uploads, active eligibility,
research OFFLINE and zero paid caps. Other conversations remain mock by default. Existing SSE/lease/cancellation and
manifest publication boundary applies. Pilot context excludes choice/evidence/memory; only new synthetic conversation
history/brief is used. Prompts remain untrusted; deterministic evidence validation applies before publication.

Fixed route: `baidu/ernie-5.5-flash-preview:free`, upstream `baidu`, official Chat Completions. Check current pricing
before each generation; prompt/completion must be explicit zero, any other advertised charge must be known zero.
No plugins/tools, routing alternatives, redirects or proxy-derived base URLs. Limit dynamic context16KiB plus fixed instructions/contract, output1024 tokens,
wire64KiB, parsed answer16KiB, request20seconds, read timeout8seconds. HTTP401/402/403/429, interruption, invalid schema,
unknown/nonzero price, changed provider/model and stale ownership never become successful mock responses.

Data disclosure: synthetic text goes via OpenRouter to Baidu; upstream terms permit storage/improvement/cross-border
processing. No account privacy changes. Consent does not establish eligibility. UI links official terms and labels
account validation separately from permitted use; actual live evaluation is T101, not technical implementation.
