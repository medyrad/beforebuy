# Stream Event Contract v1

SSE over same-origin guest session. Frames have `id`, `event`, JSON `data`; common fields: `schema_version="COPILOT-STREAM-v1"`, operation/conversation IDs، sequence، timestamp.

| Event | Payload/finality |
|---|---|
| `operation.started` | kind/bounds؛ authoritative |
| `assistant.text.delta` | provisional text only |
| `research.progress` | real stage/completed/total/domain status |
| `evidence.published` | validated evidence/snapshot IDs |
| `choice.updated` | canonical ChoiceSet pointer |
| `assistant.message.final` | final validated message pointer |
| `operation.cancelled|failed|completed` | terminal safe state |

Ordering per operation. Client deduplicates ID، rejects lower/equal sequence and reconciles gaps through REST. `Last-Event-ID` replay is bounded; REST remains authoritative. Heartbeat is not progress. No chain-of-thought، credential، raw provider/source payload or private exception.
