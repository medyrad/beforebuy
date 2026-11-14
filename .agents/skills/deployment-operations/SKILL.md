---
name: deployment-operations
description: Package and rehearse beforebuy production deployment with Docker Compose, same-origin HTTPS routing, hardened Django, PostgreSQL persistence, health checks, migrations, backup/restore, expiry cleanup, and evidence-based rollback.
---

# Beforebuy deployment operations

Use this skill only for this repository's production packaging, deployment rehearsal, or operational documentation. Keep the approved `web -> api -> db` Compose topology; do not add an orchestrator, task queue, or deployment framework.

## Required sequence

1. Read `AGENTS.md`, the constitution, `docs/handoff.md`, the active Spec Kit plan/tasks, and `references/official-sources.md`.
2. Separate packaging readiness from live-AI and public-release readiness. Never promote a local rehearsal into a production-readiness claim.
3. Write repeatable failure tests for production settings, health/readiness, and routing before implementation.
4. Build locked multi-stage images. Serve static React assets through a non-root web gateway with same-origin `/api/` proxying and SPA fallback. Run Django with Gunicorn as a non-root user.
5. Keep only the HTTPS web gateway host-published. Treat its fixed `X-Forwarded-Proto` value as trusted only because the API is isolated on the Compose network and the gateway replaces the header.
6. Supply secrets at runtime from restricted files. Require production secret, hosts, and HTTPS CSRF origins; reject debug and test switches. Keep mock/limited AI status explicit and fail closed when live configuration is incomplete.
7. Run migrations as a controlled one-shot release command before starting application workers. Back up before changing a non-empty schema.
8. Rehearse with a unique Compose project, host port, named volume, synthetic records, and local HTTPS. Never reuse or delete development volumes.
9. Exercise `pg_dump`/`pg_restore` into a separate empty volume. Run expiry cleanup before reopening, keep live AI disabled until restored accounting is reconciled, and state that retained backups can contain deleted data.
10. Identify an immutable compatible image for application rollback. For incompatible schema changes, restore the pre-migration backup; do not claim arbitrary migration reversibility.
11. Verify the host cleanup schedule configuration in addition to manually running the management command.
12. Record commands, image versions/digests, observed results, limitations, and remaining release gates. Remove local certificates, dumps, logs, and runtime secrets from project artifacts.

## Evidence rules

- A healthy container is not sufficient evidence of browser behavior; run a small real Playwright smoke.
- A management command run is not evidence that its schedule is active.
- A backup file is not evidence of recoverability; restore it and verify ownership and session access.
- Source inspection is not evidence of port isolation, persistence, or startup failure; exercise those properties.
- Never echo secret values or commit secret, key, certificate, dump, log, volume, or browser-report artifacts.
