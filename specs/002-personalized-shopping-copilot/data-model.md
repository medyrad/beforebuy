# Data Model

```text
GuestContext 1─* Conversation 1─* Message
Conversation 1─* ShoppingBrief
Conversation 1─* ResearchJob 1─* SourceSnapshot 1─* EvidenceClaim
Product 1─* Variant 1─* Offer
Conversation 1─* ChoiceSet 1─* ChoiceItem
GuestContext 1─* PreferenceMemory
GuestContext 1─0..1 UserCredential
Conversation 1─* StreamOperation 1─* StreamEvent
```

- **Conversation**: owner، status، current brief revision، generation epoch، lifecycle timestamps؛ owner-scoped.
- **Message**: role/content/uploads، `ACCEPTED|PROVISIONAL|FINAL|FAILED|CANCELLED`، operation/sequence؛ final conditional publication.
- **Upload**: owner/conversation، detected MIME، bounded size، sanitized dimensions/hash، storage reference and expiry/delete timestamps؛ original filename/metadata is not trusted or retained by default.
- **ShoppingBrief**: immutable revision، self/gift/household، category، budget/currency، uses، hard constraints، confirmed preference، candidate inference، unknowns، sources.
- **ResearchJob**: brief revision، token، limits، status/counters/times/safe failure; no raw secret/exception.
- **SourcePolicy/Snapshot**: domain policy/robots/terms/limits and canonical URL، retrieval، content metadata/fingerprint، extractor، freshness/failure.
- **Product/Variant/Offer/Claim**: stable identity/attributes/region/bundle، exact merchant observation and field-level attribution/conflict.
- **ChoiceSet/Item**: pinned brief/rank version/config، eligibility، total cost، components، coverage، tie key، reasons/unknowns.
- **PreferenceMemory**: scope/context/provenance، `CANDIDATE|CONFIRMED|REJECTED`، consent/expiry/delete; only confirmed reusable.
- **UserCredential**: fixed OPENAI provider، ciphertext/envelope/key version/masked hint/timestamps; master key external.
- **StreamOperation/Event**: revision/token/kind/status/cancel; unique monotonically sequenced versioned sanitized events.

## Retention proposal requiring approval

Conversation/message 90 days after last activity is only proposed. Upload ≤24h after extraction؛ raw research cache ≤24h؛ normalized evidence ≤conversation lifecycle؛ events 24h؛ confirmed memory until deletion with review prompt؛ credential until delete/replace؛ sanitized accounting per policy. Backup caveat required.

Indexes/constraints: owner+expiry، current brief unique، valid money/currency، evidence source XOR user message، unique authoritative variant identifier، unique operation sequence، CAS token، non-empty ciphertext and no plaintext field. Network outside DB locks.
