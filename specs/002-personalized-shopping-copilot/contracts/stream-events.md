# Stream Event Contract v1

SSE over same-origin guest session at `/api/v1/operations/{operation_id}/events`. Frames have `id` equal
`{operation_id}:{sequence}`، `event` و JSON `data`; common fields: `schema_version="COPILOT-STREAM-v1"`, operation/conversation IDs، monotonic sequence و RFC3339 timestamp. GET/reconnect never starts or restarts execution.

| Event | Payload/finality |
|---|---|
| `operation.started` | fixture kind/bounds؛ authoritative operation state |
| `assistant.text.delta` | provisional plain-text chunk، max 1024 UTF-8 bytes |
| `research.progress` | real stage/completed/total/domain status |
| `evidence.published` | validated evidence/snapshot IDs |
| `choice.updated` | canonical ChoiceSet pointer |
| `assistant.message.final` | final validated message pointer |
| `operation.cancelled` | terminal; explicit/user/delete reason |
| `operation.failed` | terminal safe code including `INTERRUPTED` |
| `operation.completed` | terminal; final message ID/revision |

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
