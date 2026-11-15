# Phase 7 Research

**Date**: 2026-11-15 — documented capability، maintainer claim و workspace measurement جدا هستند.

## Streaming

SSE از Django تا browser انتخاب می‌شود؛ command/cancel با REST است. Responses API upstream با `stream=true` semantic event می‌فرستد، اما eventهای provider مستقیماً public contract نیستند و به contract داخلی map می‌شوند. WebSocket فقط با requirement دوطرفهٔ اندازه‌گیری‌شده بررسی می‌شود.

## Phase 12 provider supersession

OpenAI-only بودن با مجوز صریح product lead لغو شد. shortlist فعلی فقط GapGPT و AvalAI است. GapGPT مدل دقیق
`gapgpt-deepseek-v4.1-flash` را با میزبانی/پردازش در ایران، Chat Completions streaming، API تجاری و تعرفهٔ
USD 0.15/M input، USD 0.015/M cached input و USD 0.60/M output مستند می‌کند؛ کیفیت فارسی، latency و invoice در این
workspace هنوز اندازه‌گیری نشده‌اند. JSON Schema/tool calling exact-model مستند نیست، پس contract فقط JSON text محدود
و validation سخت application است. AvalAI Responses و usage را دقیق‌تر مستند می‌کند، اما authorization/data path
upstream مدل‌های واسطه‌ای برای ایران حل نشده و fallback خودکار نیست. self-host روی Mac با فضای محدود و بدون مجوز
زیرساخت practical انتخاب نشد.

منابع رسمی: [GapGPT model](https://aigap.app/platform-v2/docs/models/deepseek-v4-1-flash-iran)،
[GapGPT pricing](https://aigap.app/platform-v2/pricing?model=gapgpt-deepseek-v4.1-flash)،
[GapGPT terms/privacy](https://aigap.app/rules)، [AvalAI quickstart](https://docs.avalai.ir/en/quickstart)،
[AvalAI service tiers](https://docs.avalai.ir/en/service-tiers).

## Historical OpenAI runtime (superseded only for exclusivity)

Phase 7 direct OpenAI Responses API only را تعیین کرده بود؛ Phase 12 فقط این exclusivity را supersede می‌کند. direct
OpenAI همچنان برای ایران blocked است و AvalAI feature 001 fallback خودکار نیست.

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

## Milestone B transport and extraction

Python 3.12 stdlib `http.client`/`ssl`/`socket` انتخاب شد؛ runtime dependency تازه‌ای اضافه نشد. transport خود پروژه
hostname را resolve می‌کند، همهٔ addressها را public می‌سنجد و actual socket را به IP تأییدشده pin می‌کند، درحالی‌که
TLS SNI/certificate و Host برای hostname اصلی باقی می‌مانند. proxy environment، cookie و credential مصرف نمی‌شوند؛
هر redirect دوباره exact host/path/port policy را می‌گذراند. این design در workspace با connector stub و address
assertion آزموده شد؛ performance claim عمومی ندارد.

JSON-LD Product منبع اول extractor است. fallback فقط source-specific و صریح است (در captured Technolife fixture تنها
marker availability)، و schema missing/ambiguous failure می‌دهد. نام مشابه identity نیست؛ identifier، region، capacity،
bundle، warranty و condition conflict merge را متوقف می‌کنند. sports extraction به‌دلیل source permission gap آماده نیست.

skill محلی `bounded-product-research` برای invariantهای source policy، pinned transport، provenance و lifecycle ساخته و
با validator رسمی skill-creator در project environment validate شد؛ crawler/agent framework یا workflow موازی نیست.

## Credential encryption

DB فقط envelope ciphertext/key version نگه می‌دارد و master key بیرون DB/image/Git است. decrypt فقط برای call مجاز و plaintext کوتاه‌عمر است. library/KMS پس از dependency/operations evaluation در milestone D انتخاب می‌شود؛ custom cryptography ممنوع است.

## Rejected complexity

distributed crawler، browser fleet، bypass، Celery/Redis، WebSocket پیش‌فرض، vector DB، agent framework، provider routing، self-hosted model بدون feasibility/infrastructure approval و model-generated authoritative rank.
