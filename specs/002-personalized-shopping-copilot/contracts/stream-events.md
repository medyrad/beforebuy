# Stream Event Contract v1

SSE over same-origin guest session at `/api/v1/operations/{operation_id}/events`. Frames have `id` equal
`{operation_id}:{sequence}`، `event` و JSON `data`; common fields: `schema_version="COPILOT-STREAM-v1"`, operation/conversation IDs، monotonic sequence و RFC3339 timestamp. GET/reconnect never starts or restarts execution.

| Event | Payload/finality |
|---|---|
| `operation.started` | `DEVELOPMENT_CONTEXT_FIXTURE`، `RULE_BASED_LIMITED`، `GAPGPT_CHAT_COMPLETION` or `OPENAI_RESPONSE` kind؛ authoritative operation state; provider kinds remain distinct |
| `assistant.text.delta` | provisional plain-text chunk، max 1024 UTF-8 bytes |
| `research.progress` | real stage/completed/total؛ فقط work کامل‌شده، mode و job ID مشخص |
| `evidence.published` | source ID، snapshot ID و status همان evidence unit اتمیک؛ پیش از commit دیده نمی‌شود |
| `choice.updated` | canonical ChoiceSet pointer |
| `assistant.message.final` | final validated message pointer |
| `operation.cancelled` | terminal; explicit/user/delete reason |
| `operation.failed` | terminal safe code including `INTERRUPTED` |
| `operation.completed` | terminal; conversation final-message pointer یا research job outcome/coverage |

Ordering per operation. `next_sequence - 1` is the authoritative highest issued sequence. Client deduplicates ID، rejects
lower/equal sequence and reconciles gaps through authorized `GET /api/v1/operations/{id}`. `Last-Event-ID` must belong
to the same operation; malformed/foreign values return `400 INVALID_REPLAY_ID`; a future sequence returns
`409 INVALID_REPLAY_SEQUENCE`; missing required retained history (partial or entirely purged) returns `409 REPLAY_GAP`.
Both 409 forms include the REST reconciliation URL. No-history and already-at-latest are valid; a terminal operation at
latest closes immediately. If a purge creates a gap after HTTP streaming begins، server emits non-persisted
`stream.replay_gap` with the reconciliation URL and closes; the client reads REST and never regenerates.

Event retention is 24h. Connections are admitted at at most two per application process، live for at most 45 seconds and
send `: heartbeat` at most every 15 seconds; heartbeat is connectivity only and never research progress. Expiry and stale
lease are re-read authoritatively during an open stream. Disconnect/close releases subscriber capacity exactly once.
Two subscribers read the same stored events and never duplicate execution. No chain-of-thought، credential، executable
HTML، raw provider/source payload or private exception is allowed.

Provider JSON/SSE chunks are never forwarded raw. Before provider completion the application may emit one bounded context-aware safe
lead such as «مقایسهٔ فعلی و شواهد ثبت‌شده را بررسی می‌کنم»; it contains no generated product fact. After the complete
answer plan passes candidate/value/attribution/freshness/variant validation, deterministic Persian block text may emit
as `assistant.text.delta`. `payload.phase` is `PROVISIONAL_CONTEXT` or `VALIDATED_BLOCK`; both remain provisional until
`assistant.message.final`. Unsupported blocks are omitted or become an explicit limited explanation. OpenAI output has
no artificial delay. Development scripted output uses kind `DEVELOPMENT_CONTEXT_FIXTURE` and remains visibly synthetic.
Phase 12 permits a bounded natural Persian acknowledgement/next question only after the complete plan is parsed and
validated; factual blocks still use deterministic rendering and unsupported claims are omitted.

Expired/replaced credentials, model/settings revision drift, newer turns, brief/generation edits, ChoiceSet/evidence
expiry/deletion, upload deletion and included-memory changes cannot publish. Provider failures use `GENERATION_FAILED`,
fixtures `FIXTURE_FAILED`; no raw SDK exception is sent. SDK request identifiers and usage remain private accounting
metadata, not SSE payloads.

Research eventها همان operation ledger را reuse می‌کنند. start فقط از `POST .../research` است؛ GET/status/SSE work را
شروع یا تکرار نمی‌کند. research worker با lease سی‌ثانیه‌ای و request حداکثر بیست‌ثانیه‌ای قبل و بعد I/O renew/recheck
می‌کند. هر evidence unit و completion با lock order
`Conversation → StreamOperation → ResearchJob → SourcePolicy` منتشر می‌شوند؛ snapshot/identity/offer/claims/counters و
`evidence.published`/progress یک commit دارند و source failure موفقیت source دیگر را پاک نمی‌کند.
