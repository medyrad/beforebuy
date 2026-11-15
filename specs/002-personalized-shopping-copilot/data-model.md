# Data Model

## Milestone D implementation

Migrations 0011–0014 add owner-scoped settings, preference memory, encrypted credentials, credential revision
snapshots and durable session accounting. `CopilotSettings` is one-to-one with GuestContext (memory default false,
selected documentation model and CAS revision). `Conversation.temporary` is immutable at creation.

`PreferenceMemory` holds category and a whitelisted structured criterion (field/expected/kind/scope), source
conversation/revision, state and CAS revision. Source deletion cascades the row. Candidate expiry defaults to seven
days from creation; first confirmation sets a non-sliding 90-day bound, limited by owner and source expiry. Editing
does not renew it. These settings are provisional development policy requiring product review before release.

`UserCredential` stores ciphertext and a separately wrapped random data key, revision UUID, state and expiry (default
30 days from save/replace, capped by owner access). No plaintext or key suffix is stored/returned. Master keyring is a
runtime file outside DB/Git/images. Saving sets STORED_UNVALIDATED; no authorized validation exists in this phase.

`StreamOperation.credential_revision` snapshots the accepted key version. Replace/delete cancels dependent queued
and running operations; callbacks and final publication reject stale/expired credentials. Requests already sent
cannot be recalled. Memory application stores an independent action receipt, not a pointer to deletable memory.

Phase 11.1 adds `context_fingerprint` and `context_manifest` to conversation StreamOperation rows. The manifest is a
bounded set of IDs/revisions/hashes only: user turn, latest accepted turn, brief/generation, settings/model, ChoiceSet
and evidence snapshots, upload hashes and included memory revisions/expiries. It deliberately excludes message text,
profile prose, raw source content and credentials. The provider payload is assembled ephemerally; final publication
revalidates every manifest anchor and rejects stale/deleted/expired context.

`GuestContext.copilot_reserved_microusd` and `copilot_spent_microusd` are durable aggregates maintained by the existing
LiveBudgetLedger. Guest -> daily window -> invocation is the lock order. Settlement is idempotent and known usage
is not clipped; missing usage uses its reservation allowance. Purging 90-day invocation metadata does not reset
session spending. Aggregates expire with the owner and are not reset by credential/model/memory changes.

The migration backfills retained Copilot invocations. No historical live Copilot use is authorized; deleted historic
metadata cannot be reconstructed. Any future restoration/activation must reconcile accounting before spending.

```text
GuestContext 1─* Conversation 1─* Message
Conversation 1─* ShoppingBrief
Conversation 1─* ResearchJob 1─* SourceSnapshot 1─* EvidenceClaim
Product 1─* Variant 1─* Offer
Conversation 1─* ChoiceSet (immutable result items embedded as JSON)
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
- **ChoiceSet**: migration 0010؛ owner از Conversation، pinned brief_revision/generation_epoch/rule_version، immutable result JSON شامل item/check/evidence/coverage/unknown/offer، snapshot_ids و evidence_valid_until. جدول ChoiceItem تکراری ساخته نمی‌شود. همراه conversation حذف/منقضی می‌شود؛ read/compare/demo retention را تمدید نمی‌کنند. `ShoppingBrief.comparison` فقط ترجیحات صریح همین گفت‌وگوست، نه memory.
- **PreferenceMemory**: scope/context/provenance، `CANDIDATE|CONFIRMED|REJECTED`، consent/expiry/delete; only confirmed reusable.
- **UserCredential**: fixed OPENAI provider، ciphertext/wrapped key/revision/state/timestamps; fixed UI mask (no stored suffix); master key external.
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
