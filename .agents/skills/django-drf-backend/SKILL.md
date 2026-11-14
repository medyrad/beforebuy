---
name: django-drf-backend
description: Implement or review this project's Django/DRF backend, especially guest ownership, explicit anonymous CSRF, PostgreSQL transactions, migrations, API contracts, and behavioral tests.
---

# Django/DRF Backend

Use this skill only for backend work in Purchase Regret Predictor. Read the feature spec, plan, data model, OpenAPI
contract and constitution first. Apply `test-driven-development` to behavior changes and use PostgreSQL—not SQLite—for
transaction/concurrency claims.

## Required boundaries

- Keep one Django modular monolith and one domain app. Do not add JWT, accounts, repository/unit-of-work layers,
  async frameworks, queues, caches or generic provider registries without a new approved requirement.
- Treat every analysis/feedback lookup as `guest_context + active expiry + identifier`; an object ID is never authority.
- Keep `CsrfViewMiddleware` enabled. DRF `SessionAuthentication` does not enforce CSRF for anonymous requests, so
  explicitly apply Django `csrf_protect` to every unsafe API view and use `ensure_csrf_cookie` on bootstrap. Test with
  CSRF enforcement enabled, including missing/invalid/valid token and configured Host/Origin behavior.
- Use Django database sessions. Extend guest/session access only when a new analysis is persisted, up to that analysis's
  immutable expiry. Reads, edits, retries and feedback never extend analysis retention.

## Validation and contracts

- Serializer validation handles API shape; pure domain validation owns money normalization and rubric semantics; DB
  constraints defend positive revisions, valid money/rating ranges and relationships.
- Return the OpenAPI error envelope consistently. Foreign, deleted and expired resources all use non-enumerating 404;
  stale input/report/operation state uses 409.
- Never infer product facts from model text. Persist typed evidence and validated templates only; raw provider payloads,
  session keys, answers and ratings do not enter logs.

## Transactions and migrations

- Do network/provider work outside transactions. Use short `transaction.atomic()` blocks and row locks only at final
  state transitions.
- Initial publication and clear-history serialize on `GuestContext`: capture `generation_epoch`, then lock/recheck at
  publish; clear locks, increments epoch and deletes. A check followed by insert outside the same transaction is invalid.
- Each edit/retry records a new operation token conditionally against current input/report revision. Only the current
  token may publish or clear feedback; older responses are discarded/conflicted.
- Migrations must be deterministic and reviewed with `makemigrations --check`; test applying them to an empty PostgreSQL
  database. Never edit an applied migration to change behavior.

## ORM and tests

- Prefer explicit QuerySets/services over generic repositories. Use `select_related` for current report/feedback list
  reads and inspect query behavior when adding loops.
- Hand-author expected rubric/scenario cases; exhaustive enumeration is an additional invariant, not the sole oracle.
- Race tests use controlled barriers/events and separate database connections. Avoid sleep as the primary synchronizer.
- Test migrations/checks, owner isolation with independent clients, expiry at the exact boundary, purge, CSRF, revision
  conflicts, clear/create epoch, competing retries and rating invalidation.

## Primary references

- Django CSRF: <https://docs.djangoproject.com/en/5.2/howto/csrf/>
- Django sessions: <https://docs.djangoproject.com/en/5.2/topics/http/sessions/>
- Django transactions: <https://docs.djangoproject.com/en/5.2/topics/db/transactions/>
- DRF authentication/anonymous CSRF caveat: <https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication>
- DRF serializers: <https://www.django-rest-framework.org/api-guide/serializers/>
- Django testing: <https://docs.djangoproject.com/en/5.2/topics/testing/>
