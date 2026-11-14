---
name: purchase-regret-project
description: Keep work on Purchase Regret Predictor aligned with its product decisions, Spec Kit artifacts, phase boundary, and evidence requirements. Use for any substantive task in this repository.
---

# Purchase Regret Project

Before acting:

1. Read `docs/product-brief.md`, `docs/decisions.md`, and `.specify/memory/constitution.md`.
2. Read the relevant feature specification under `specs/` when one exists.
3. Classify each relevant statement as an approved decision, proposed default, unvalidated assumption,
   or open question. Do not silently promote its status.
4. Follow the installed `$speckit-*` workflow for specification-driven work. Do not create a competing
   planning or task system.
5. Confirm the authorized phase and keep changes inside it. Escalate consequential unresolved product
   decisions instead of inventing them.

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
  client logic may only control presentation and the documented questionnaire flow.
- Do not persist answers or ownership data in local/session storage. Use the real same-origin guest API,
  its CSRF cookie/header contract, and abort or ignore stale requests.
- Scope upstream frontend guidance to client-side React/Vite. Do not introduce Next.js, SSR/RSC,
  server actions, Vercel services, or deployment requirements.
