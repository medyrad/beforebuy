# Quickstart — Milestone A/B offline and fixture stack

1. After reviewing `.env`, run `docker compose up -d db`, then `docker compose run --rm api python backend/manage.py
   migrate --noinput`, then `docker compose up --build -d`. Compose builds React, starts Django/PostgreSQL and exposes
   the complete offline stack through NGINX; no host npm process is required and no volume is reset.
2. Open `http://127.0.0.1:58080/copilot`. The legacy feature remains at `/` and direct refresh of `/copilot` uses the
   SPA fallback.
3. Create a conversation, explicitly edit/confirm its brief, send a message and observe real fixture deltas through
   NGINX. The UI must display «حالت توسعه / fixture» and must not show invented products, prices or citations.
4. Stop an active operation, reconnect, and verify REST reconciliation. GET/SSE never start or restart work. A service
   restart may terminalize an in-flight fixture as `INTERRUPTED`; it never silently resumes. Each SSE connection is
   bounded to 45 seconds and reconnects from its last event. Missing retained history or a purge race reconciles with
   `GET /api/v1/operations/{id}` instead of re-running the fixture. Only two subscribers per process are admitted so
   status/cancel requests retain request-thread capacity.
5. Upload at most three JPEG/PNG/WebP images, each ≤5 MiB, ≤4096px per side and ≤12MP. Bytes are decoded/re-encoded,
   metadata removed, stored in PostgreSQL, owner-authorized and expired within 24h.
6. Run the canonical backend suite from the repository root with `./scripts/test-backend.sh`; run frontend checks inside
   the web build or locally with the locked Node dependencies.

## Reproducible Milestone B fixture API smoke

Default Compose remains `BEFOREBUY_RESEARCH_MODE=OFFLINE`; research start returns `409 RESEARCH_OFFLINE` and performs
zero outbound requests. For a local, explicitly fixture-labelled smoke (never current market data):

```sh
BEFOREBUY_RESEARCH_MODE=FIXTURE docker compose up --build -d
docker compose exec api python backend/manage.py migrate --noinput
```

Bootstrap `GET /api/v1/session` and retain its cookie/CSRF token؛ `POST /api/v1/conversations`؛ `PATCH` the brief with
recipient/category/budget/use case؛ `POST .../brief/confirm`؛ then:

```http
POST /api/v1/conversations/{conversation_id}/research
Idempotency-Key: research-smoke-key-0001
X-CSRFToken: {token}
Content-Type: application/json

{"expected_brief_revision":1,"source_ids":["synthetic-appliance-v1","synthetic-electronics-v1"]}
```

Poll `GET /api/v1/research-jobs/{job_id}` or follow the returned operation `events_url`. Expected terminal fixture result:
`SUCCESS`, `fixture_labeled=true`, two snapshots with `canonical_url=null` and explicit `fixture_label`. GET/status/replay
does not start work. To cancel, `POST /api/v1/research-jobs/{job_id}/cancel` with CSRF. To restore the safe default:

```sh
docker compose up -d --force-recreate api
```

with `BEFOREBUY_RESEARCH_MODE` unset/`OFFLINE`. `LIVE` currently has zero enabled source policy and must report
`NO_SUPPORTED_SOURCES`; it must not silently emit fixture evidence.

No public deployment, provider call, broad crawl, product ranking, memory or credential storage belongs to Milestone B.
