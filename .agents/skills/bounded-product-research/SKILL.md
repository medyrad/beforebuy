---
name: bounded-product-research
description: Implement or review Beforebuy source policy, safe HTTP retrieval, deterministic product extraction, provenance, identity, caching, and bounded research-job lifecycle. Use only for public read-only product research, not broad crawling or ranking.
---

# Bounded Product Research

Read the active feature specification, source register, data model, contracts, and approved limits before changing retrieval code. Keep fixture readiness, captured real-source extraction, live probe success, repeatable live extraction, and enabled integration as separate states.

## Source and transport boundary

- Enable only exact domains and paths with reviewed redirect destinations, access observations, freshness, pacing, retention, and display constraints. Robots observations are evidence, not a license grant.
- Reject non-HTTP(S), embedded credentials, unsupported ports, ambiguous hosts, and loopback/private/link-local/reserved/metadata destinations for every initial URL and redirect.
- Resolve first, filter every address, and bind the actual connection to one approved resolved address while retaining the original hostname for TLS SNI, certificate verification, and `Host`. Do not perform an unconstrained second DNS lookup or inherit ambient proxies.
- Bound total requests, redirects, decoded bytes, MIME, body time, job deadline, per-domain pacing, and concurrency. Count policy checks, retries, and redirects. Honor `Retry-After` only inside the remaining deadline.
- Keep network work outside database transactions and treat all returned content as untrusted data, never as instructions.

## Evidence and identity

- Prefer documented structured data, then explicit source-specific fallback parsing with schema checks. Fixtures are minimal, copyright-conscious, checksummed, and never described as current market data.
- Persist the exact canonical URL, retrieval time, response fingerprint, extractor/version, source role, product/variant identity, normalized field/value/unit, permitted minimal support location, and unknown/conflicting/stale state.
- Manufacturer specifications remain attributed claims, not independent performance measurements. Merchant observations keep item price, shipping, total payable, seller, condition, warranty/registration, availability, and retrieval time separate.
- Parse Persian/Arabic/Latin digits and rial/toman explicitly. Unknown currency, shipping, stock, or identity stays unknown. Never merge on similar names alone.

## Jobs, cache, and ownership

- Research starts only through an explicit unsafe command with owner and CSRF checks. Identical active submissions deduplicate; GET, replay, and status never start work.
- Reuse the existing operation/event publication boundary and lock order. Renew a still-valid owned lease during long work; never revive an expired lease or hold a lock across I/O.
- Recheck owner, conversation expiry, brief revision, cancellation, generation epoch, and lease before each publication. Partial success preserves valid evidence and states coverage gaps honestly.
- Raw cache has a fixed creation-based expiry; a hit retains the original retrieval timestamp. Conversation evidence is owner-scoped and cannot outlive its conversation. Cleanup must distinguish private orphaned data from shared public records still referenced by active owners.
- A process-local semaphore is not a deployment-global guarantee. Document that limit and keep research admission from consuming cancel/status capacity.

Use PostgreSQL barriers/events for concurrency tests, a test-only local transport boundary for controlled private-address fixtures, and separate opt-in commands for any live public probes. Normal suites must make zero public requests.
