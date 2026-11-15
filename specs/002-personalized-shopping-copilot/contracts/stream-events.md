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

Ordering per operation. Client deduplicates ID، rejects lower/equal sequence and reconciles gaps through authorized
`GET /api/v1/operations/{id}`. `Last-Event-ID` must belong to the same operation; malformed/foreign values return
`400 INVALID_REPLAY_ID`. If requested sequence predates retained history, SSE returns `409 REPLAY_GAP` with REST
reconciliation URL. Event retention is 24h. `: heartbeat` comment is connectivity only and is never research progress.
Two subscribers read the same stored events and never duplicate execution. No chain-of-thought، credential، executable
HTML، raw provider/source payload or private exception is allowed.
