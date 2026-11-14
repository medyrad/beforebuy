# Phase 7 Research

**Date**: 2026-11-15 — documented capability، maintainer claim و workspace measurement جدا هستند.

## Streaming

SSE از Django تا browser انتخاب می‌شود؛ command/cancel با REST است. Responses API upstream با `stream=true` semantic event می‌فرستد، اما eventهای provider مستقیماً public contract نیستند و به contract داخلی map می‌شوند. WebSocket فقط با requirement دوطرفهٔ اندازه‌گیری‌شده بررسی می‌شود.

## OpenAI runtime

Feature 002 direct OpenAI Responses API only است؛ AvalAI feature 001 fallback نیست. exact model ID در implementation پس از بررسی model catalog، text/image، structured output، streaming، context و price انتخاب می‌شود. در 2026-11-15 ایران در فهرست supported countries OpenAI نیست؛ live calls با users/backend ایران blocked و calls این phase صفر است.

`store=false` application-state را محدود می‌کند ولی abuse-monitoring retention یا ZDR را تضمین نمی‌کند. key user-owned eligibility را ثابت نمی‌کند و ChatGPT subscription از API billing جداست.

منابع رسمی: [Responses](https://developers.openai.com/api/reference/responses/overview)، [streaming](https://developers.openai.com/api/docs/guides/streaming-responses)، [vision](https://developers.openai.com/api/docs/guides/images-vision)، [data](https://developers.openai.com/api/docs/guides/your-data)، [keys](https://developers.openai.com/api/docs/guides/api-keys)، [pricing](https://developers.openai.com/api/docs/pricing)، [regions](https://help.openai.com/en/articles/5347006-which-countries-and-territories-are-supported-by-openai).

## Design skill evaluation

Official Anthropic revision `1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064`:

| Candidate | Result |
|---|---|
| `frontend-design` | selected/installed project-locally؛ Apache-2.0، docs-only، no runtime dependency؛ overlay فارسی/RTL مقدم است |
| `web-artifacts-builder` | rejected؛ React 18/Parcel/Tailwind/shadcn stack موازی و dependency غیرضروری |

Vercel snapshots inactive ماندند. current-turn catalog پیش از install ساخته شده بود؛ files/frontmatter/license/path validate شدند و native catalog discovery باید در session بعد تأیید شود.

## Source strategy

manufacturer specs، merchant offers و review/editorial claims types جدا دارند. robots observation permission حقوقی جامع نیست؛ terms و response واقعی هر domain لازم است. measurement محدود در [source-feasibility.md](source-feasibility.md) آمده است.

## Credential encryption

DB فقط envelope ciphertext/key version نگه می‌دارد و master key بیرون DB/image/Git است. decrypt فقط برای call مجاز و plaintext کوتاه‌عمر است. library/KMS پس از dependency/operations evaluation در milestone D انتخاب می‌شود؛ custom cryptography ممنوع است.

## Rejected complexity

distributed crawler، browser fleet، bypass، Celery/Redis، WebSocket پیش‌فرض، vector DB، agent framework، multi-provider، self-hosted model و model-generated authoritative rank.
