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

- **Conversation**: owner، status، current brief revision، generation epoch، `last_eligible_activity_at` و expiry؛ owner-scoped. expiry دقیقاً 90 روز پس از آخرین user message پذیرفته‌شده یا brief edit/confirmation است.
- **Message**: role/content/uploads، `ACCEPTED|PROVISIONAL|FINAL|FAILED|CANCELLED`، operation/sequence؛ final conditional publication. read/replay/generator event زمان conversation را تمدید نمی‌کند.
- **Upload**: owner/conversation، detected MIME، bounded sanitized bytes در PostgreSQL، dimensions/hash، expiry/delete timestamps؛ original filename/metadata نگهداری نمی‌شود. expiry حداکثر 24 ساعت از creation و مستقل از extraction است.
- **ShoppingBrief**: current compare-and-swap revision، self/gift/household، category، budget/currency، uses، hard constraints، confirmation، contradictions، unknowns و provenance نسخه‌دار. Milestone A history از provenance Message/explicit edit قابل ردیابی است؛ snapshotهای immutable کامل در milestone بعد فقط با نیاز مصوب اضافه می‌شوند.
- **ResearchJob**: owner conversation، brief revision/generation epoch، operation، idempotency hash، exact `{source_id,url}` targets، immutable limits، status/times/coverage/safe failure و شمارنده‌های واقعی request/redirect/wire/decoded؛ no raw secret/exception. فقط یک job فعال per guest.
- **SourcePolicy/Snapshot**: exact domain/port/path و per-destination redirect policy، robots/terms/readiness/limits و canonical product URL، retrieval، content metadata/fingerprint، extractor، freshness/failure. raw bytes حداکثر 24h و non-sliding هستند؛ snapshot خصوصی با conversation cascade می‌شود.
- **Product/Variant/Offer/Claim**: stable identity/attributes/region/bundle، exact merchant observation and field-level attribution/conflict. Phase 9.2 offer original amount/currency را از normalized `price_toman` جدا، merchant/source URL، `COMPARISON_OBSERVED|MERCHANT_PAGE_VERIFIED`، shipping/mandatory-charge unknown، warranty/condition و observed/freshness state را حفظ می‌کند. same seller/offer در API view deduplicate می‌شود و raw discrepancy حذف نمی‌شود.
- **ChoiceSet/Item**: pinned brief/rank version/config، eligibility، total cost، components، coverage، tie key، reasons/unknowns.
- **PreferenceMemory**: scope/context/provenance، `CANDIDATE|CONFIRMED|REJECTED`، consent/expiry/delete; only confirmed reusable.
- **UserCredential**: fixed OPENAI provider، ciphertext/envelope/key version/masked hint/timestamps; master key external.
- **StreamOperation/Event**: revision/token/kind/status/cancel، idempotency key/request hash، lease owner/expiry و terminal reason؛ eventها sequence یکتا و expiry 24 ساعته دارند. operation/message authoritative تا conversation expiry باقی می‌ماند.

Phase 9.3: `request_count` conservatively includes each connection fallback in the existing request/domain cap.
Source review timestamps are observation evidence, never refreshed by toggles; unknown exact times stay null with
date-precision evidence in access notes. `live_enabled` is independent of `readiness`.

## Approved Milestone A/B retention

مصوب Milestone A: Conversation، Message و current Brief revision برابر 90 روز پس از آخرین user message پذیرفته‌شده یا
brief edit/confirmation منقضی می‌شوند. read/list/SSE/replay/retry خودکار/event/background این anchor را تمدید نمی‌کند.
Upload حداکثر 24 ساعت از creation و StreamEvent دقیقاً 24 ساعت نگه‌داری می‌شود. نبود replay با REST reconcile می‌شود،
نه regeneration. حذف conversation فوراً access و late publication را با generation epoch/token باطل می‌کند. purge
command bytes و expired rows را حذف می‌کند؛ backupهای از قبل ساخته‌شده طبق backup policy age out می‌شوند و حذف فوری
از backup وعده داده نمی‌شود. در Milestone B raw response حداکثر 24 ساعت از retrieval نگه‌داری می‌شود و read آن expiry را تمدید نمی‌کند؛ normalized private evidence بیش از conversation مالک باقی نمی‌ماند. offer freshness per source مستقل از cache expiry است. Memory/credential retention خارج Milestone B است. feature 001 lifecycle تغییر نمی‌کند.

Indexes/constraints: owner+expiry، current brief unique، valid money/currency، evidence source XOR user message، unique authoritative variant identifier، unique operation sequence، CAS token، non-empty ciphertext and no plaintext field. Network outside DB locks.

Phase 9.1 publication unit زیر lock order `Conversation → StreamOperation → ResearchJob → SourcePolicy` پس از I/O
ساخته می‌شود و snapshot/product/variant/offer/claims/counters/events را در یک transaction ذخیره می‌کند. rollback، cancel،
lease loss، brief/generation drift یا expiry هیچ evidence یا identity orphan تازه‌ای باقی نمی‌گذارد. Migration
`0007_research_targets_and_transport_counters` jobهای قدیمی را بدون network یا reinterpretation به targetهای URL-null
منتقل می‌کند.
