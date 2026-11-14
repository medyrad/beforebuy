---
name: purchase-regret-project
description: Keep Beforebuy work aligned with its active Shopping Copilot direction, preserved legacy feature, Spec Kit artifacts, phase boundaries, and evidence requirements. Use for substantive tasks in this repository.
---

# Beforebuy Project Context

Before acting:

1. Read `docs/product-brief.md`, `docs/decisions.md`, and `.specify/memory/constitution.md`.
2. Read the relevant feature specification under `specs/` when one exists.
3. Classify each relevant statement as an approved decision, proposed default, unvalidated assumption,
   or open question. Do not silently promote its status.
4. Follow the installed `$speckit-*` workflow for specification-driven work. Do not create a competing
   planning or task system.
5. Confirm the authorized phase and keep changes inside it. Escalate consequential unresolved product
   decisions instead of inventing them.

Feature `002-personalized-shopping-copilot` is the current product direction. Feature `001-purchase-decision-analysis`
is preserved legacy evidence and may coexist until an explicit cutover; do not rewrite its history or mark its `T039`
complete from work on feature 002. For feature 002, keep conversation, bounded research, Choice Desk, opt-in memory,
direct OpenAI eligibility, and source readiness as separate gates. A user-owned key does not bypass region support.

When changing the project, record consequential decisions in `docs/decisions.md` and update every
affected Spec Kit artifact. Use the relevant domain and verification skills. Report only checks that
actually ran, with their command and result; distinguish mock AI from live-provider behavior.

## Project-owned React/Vite/RTL overlay

This overlay is original project guidance derived from the project's requirements and official React, Vite and WAI
documentation. The inactive Vercel snapshots are provenance-only and must not be invoked or treated as licensed input.

For the React + TypeScript + Vite client:

- Keep `lang="fa"` and `dir="rtl"` at the document root. Use semantic DOM order, visible labels,
  keyboard/focus support, text in addition to color, and `aria-live` only for meaningful status changes.
- Localize user-facing API enums and identifiers. Use an LTR isolate such as `<bdi dir="ltr">` only
  for mixed-direction model names, identifiers, and other genuinely LTR fragments.
- Treat whole-toman inputs as text with numeric input hints. Preserve the distinction between budget
  `0` and explicit unknown, retain user input after validation errors, and show actionable Persian errors.
- Do not reproduce the rubric or infer outcomes in the browser. The backend report is authoritative;
  client logic may only control presentation and the documented flow. For Choice Desk, deterministic ranking and
  evidence publication remain backend-authoritative; streamed deltas are provisional until finalized.
- Do not persist answers or ownership data in local/session storage. Use the real same-origin guest API,
  its CSRF cookie/header contract, and abort or ignore stale requests.
- Scope upstream frontend guidance to client-side React/Vite. Do not introduce Next.js, SSR/RSC,
  server actions, Vercel services, or deployment requirements.
- When using the project-local `frontend-design` skill, apply `choice-desk-design.md` as the mandatory Persian/RTL,
  accessibility, evidence, reduced-motion, and existing-stack overlay. Do not add its rejected artifact-builder stack.
