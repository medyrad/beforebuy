# فهرست ابزارها و مهارت‌ها

## سیاست انتخاب

Spec Kit تنها مالک SDD است. قابلیت مستندشده توسط maintainer، ادعای performance او و نتیجه واقعاً اندازه‌گیری‌شده در این workspace با هم خلط نمی‌شوند. نصب‌ها تا حد ممکن project-scoped، pin‌شده و قابل بازسازی‌اند. ابزار فاز آینده پیش از trigger همان فاز نصب نمی‌شود.

## محیط مشاهده‌شده در Phase 0

| Capability | Result |
|---|---|
| Git | `2.23.0` |
| Python | `python3 3.12.4`; فرمان `python` موجود نبود |
| uv / uvx | `0.13.0` |
| Node.js / npm | `20.19.0` / `10.8.2` |
| pnpm / Bun | `9.15.0` / `1.3.9` |
| Yarn | pre-activated نبود؛ Corepack برای download prompt داد و استفاده نشد |
| Docker / Compose | `28.1.1` / `v2.35.1-desktop.1` |
| Codex CLI | `0.154.0-alpha.6.1` از VS Code extension |

نصب project-scoped Spec Kit در این ماشین حدود چهار دقیقه زمان build فعال داشت و به‌دلیل نبود wheel
سازگار، `cryptography` را با Rust از source ساخت. این مشاهده فقط setup effort همین workspace است و ادعای
performance عمومی نیست. dependency برنامه‌ای نصب نشد.

## Inventory

| Need | Selected tool/skill | Alternatives | Evidence | Version/commit | Local path | License | Install phase | Verification | Reason for deferral |
|---|---|---|---|---|---|---|---|---|---|
| SDD workflow | GitHub Spec Kit + Codex integration | ابزار برنامه‌ریزی موازی انتخاب نشد | مستندات رسمی نصب و integration؛ release رسمی. Phase 4 همان feature canonical را analyze و implement کرد و اجرا فقط به پنج task M2 محدود شد. | `v1.4.0`, `14ddec8cb22db2a3b50e5ae6861b31053f132bfa`; workflows `1.0.1` | `.tools/` (ignored), `.specify/`, `.agents/skills/speckit-*` | MIT | Phase 0 تا Phase 4 M2 | analyze: ۴۴ requirement، پوشش ۱۰۰٪، critical صفر؛ checklistها 30/30 و 25/25 | M3–M4 deferred |
| Systematic debugging | Superpowers `systematic-debugging` | راهنمای custom؛ debugging ad hoc | maintainer workflow چهارمرحله‌ای و root-cause tracing را مستند کرده است؛ performance claim آن مبنی بر سریع‌تر بودن روش اندازه‌گیری نشد. در M2 برای validation رقم فارسی، race وضعیت feedback، و focus لینک پرش root-cause tracing انجام شد. | `22f0b463e7a5e579904dd6211a520321035526f7` | `.agents/skills/systematic-debugging` | MIT | Phase 0 | metadata معتبر؛ سه regression واقعی با test/browser evidence اصلاح شدند | — |
| Verification before completion | Superpowers `verification-before-completion` | فقط AGENTS.md؛ check دستی | maintainer اجرای command تازه و خواندن output پیش از claim را الزام می‌کند؛ در این فاز checklist نهایی با commandهای واقعی اجرا شد. | `22f0b463e7a5e579904dd6211a520321035526f7` | `.agents/skills/verification-before-completion` | MIT | Phase 0 | metadata valid؛ checkهای تازه در handoff ثبت شدند | — |
| Behavioral testing guidance | Superpowers `test-driven-development` | راهنمای custom؛ test-after | maintainer red/green/refactor و آزمون رفتار واقعی را مستند کرده است. ادعاهای سرعت/اعتماد اندازه‌گیری نشده‌اند. scope آن فقط implementation رفتار/bugfix است، نه prose/config. | `22f0b463e7a5e579904dd6211a520321035526f7` | `.agents/skills/test-driven-development` | MIT | Phase 0 | metadata معتبر؛ در M2 regression ردِ نادرست رقم فارسی ابتدا red و سپس green شد | — |
| Code review | فایل محلی Codex system `review-agent`؛ در Phase 1 native-discoverable نبود | Superpowers `requesting-code-review` و `receiving-code-review` | فایل read-only review در مسیر قبلی همچنان موجود است، اما catalog بومی skillهای Phase 1 نام آن را ارائه نکرد؛ بنابراین review-agent در این فاز invoke یا credited نشد. quality review با checklistهای Spec Kit و inspection مستقیم انجام شد. | bundled with current Codex extension; مستقل pin نشده | `/Users/mehdi/.codex/skills/.system/review-agent` | همراه distribution محلی؛ license مستقل در فایل مهارت اعلام نشده | موجود روی disk، availability بومی تاییدنشده | file presence تایید؛ native discovery absent؛ هیچ review-agent run ادعا نمی‌شود | نصب workflow تکراری همچنان توجیه ندارد |
| Consequential product questions | `grill-me` + dependency `grilling` | مصاحبه آزاد؛ سؤال‌های ad hoc | repository نشان داد `grill-me` wrapper و `grilling` dependency واقعی آن است؛ روش design tree/frontier مستند است. این پروژه interview را به حداکثر ۵ سؤال consequential محدود می‌کند. wrapper برای Codex patch شد: کلید frontmatter نامعتبر حذف و generic Skill-tool call به sibling skill تبدیل شد؛ explicit-only policy حفظ شد. | repo `1.3.2`, commit `5863806dd4e15c63174bee4e7515a4256792ecfa` + local compatibility patch | `.agents/skills/grill-me`, `.agents/skills/grilling` | MIT | Phase 0 | metadata/dependency، validator و سؤال‌های handoff | — |
| Project context | custom `purchase-regret-project` | تکرار context در هر prompt | brief پروژه نیازهای non-obvious درباره وضعیت تصمیم‌ها، scoring، phase boundary و verification دارد؛ skill به اسناد authoritative ارجاع می‌دهد. | repository-local, initial Phase 0 revision | `.agents/skills/purchase-regret-project` | Project source | Phase 0 | `quick_validate.py` با PyYAML ephemeral موفق؛ همه reference pathها موجود | — |
| Frontend implementation | راهنمای project-owned در `purchase-regret-project` با منابع رسمی React، Vite و WAI | snapshotهای `react-best-practices` و `web-design-guidelines` از Vercel Labs | snapshotهای upstream در Phase 4 بررسی شدند، اما tree دقیق revision پین‌شده هیچ `LICENSE`/`NOTICE`/`COPYING` نداشت؛ metadata یکی از skillها به‌تنهایی متن grant نیست و دیگری declaration مجوز هم ندارد. بنابراین هر دو snapshot از Phase 5 inactive هستند و نه invoke می‌شوند، نه مبنای تغییر تازه، و نه برای redistribution مجاز فرض می‌شوند. الزامات React+Vite، RTL فارسی و دسترس‌پذیری در skill بومی پروژه حفظ شده‌اند. | راهنمای بومی: repository-local Phase 5؛ snapshot provenance: `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` | `.agents/skills/purchase-regret-project`; snapshotهای inactive در `.agents/skills/react-best-practices` و `.agents/skills/web-design-guidelines` | Project source؛ upstream snapshot نامشخص | راهنمای بومی از Phase 5؛ snapshotها در Phase 4 | lint، component و browser checks Phase 4؛ provenance با GitHub tree دقیق بازبینی شد | snapshotها فقط تا روشن‌شدن مجوز برای provenance نگه داشته شده‌اند |
| Backend implementation | custom project-local `django-drf-backend` | `nimadorostkar/Claude-Skills-collection`; `Jeffallan/django-expert` 1.1.0؛ `vintasoftware/django-ai-plugins` | candidateها broad/dependency-heavy یا متکی به JWT/Django قدیمی‌تر بودند. skill محلی فقط validation، guest ownership، explicit anonymous CSRF، migration، ORM/transaction، API contract و PostgreSQL tests را پوشش می‌دهد. | repository-local Phase 3 revision | `.agents/skills/django-drf-backend` | Project source | Phase 3 M1 | `quick_validate.py` → `Skill is valid!`؛ سپس در endpoint/migration/race tests استفاده شد | — |
| Browser verification | Playwright CLI + skill رسمی + `@playwright/test` | Playwright MCP؛ browser exploration تنها | CLI snapshot/requests برای inspection و runner برای journeyهای repeatable استفاده شد؛ MCP capability لازم اضافه‌ای نداشت. bundled Chromium روی macOS 12 پشتیبانی نشد، پس channel رسمی Chrome نصب‌شده انتخاب شد. license کامل در `third_party/licenses/playwright-Apache-2.0.txt` حفظ شد. | Playwright `v1.65.1`, tag commit `bbd948344ea9a60bf1e6f125c02ca99b2b51593b`; Chrome channel | `.agents/skills/playwright-cli`; `frontend/` | Apache-2.0 | Phase 4 M2 | CLI inspection واقعی؛ `6 passed` روی Django/PostgreSQL؛ axe serious/critical صفر در دو viewport | MCP deferred؛ مرورگر bundled به‌علت host OS unavailable |
| AI implementation | `purchase-ai-analysis` + OpenAI Python SDK transport for AvalAI Responses | Google GenAI SDK؛ direct OpenAI؛ provider framework | skill بومی contract ساخت‌یافته، evidence/unknown، مرز scoring قطعی، failure/cost و evaluation را بدون framework اضافی پوشش می‌دهد. AvalAI `gpt-5.6-luna` candidate ایران است؛ direct OpenAI غیرفعال و کیفیت فارسی/latency هنوز اندازه‌گیری نشده‌اند. | skill repository-local Phase 5؛ مدل `gpt-5.6-luna`؛ SDK `3.49.0` | `.agents/skills/purchase-ai-analysis`; dependency project-scoped | Project source؛ SDK Apache-2.0 | Phase 5 M3/5.1/5.2 | contract/stub/accounting suites و backend regression؛ live calls `0` | live evaluation و human review تا provider clarification، credential/credit مجاز و cap صریح deferred است |
| Deployment | project-local `deployment-operations` + Docker Compose | platform-specific deployment skills؛ deployment framework | راهنمای کوچک بر مستندات رسمی Django 5.2، Docker Compose/multi-stage/secrets، PostgreSQL 18 و NGINX unprivileged تکیه دارد؛ topology مصوب را بدون service/framework تازه پوشش می‌دهد. | skill repository-local Phase 6؛ Docker `28.1.1`، Compose `2.35.1`؛ Python `3.12.12`، Node `24.11.0-alpine3.22`، NGINX unprivileged `1.30.6`، PostgreSQL `18.1` با digestهای ثبت‌شده در Dockerfile/Compose | `.agents/skills/deployment-operations` | Project source؛ NGINX unprivileged Apache-2.0؛ imageهای official/vendor | Phase 6 M4 | build قفل‌شده، production settings 6/6، health/HTTPS/browser، restart persistence، fresh/prior migration، dump/restore، image rollback و host-scheduled cleanup | public deployment، target-host systemd activation و live AI pending |
| Code intelligence | هیچ ابزار اولیه نصب نشده؛ بعداً حداکثر دو گزینه از Graphify، codebase-memory-mcp، Serena و GitNexus مقایسه می‌شوند | native `rg`, Git و language tooling | trigger: پس از vertical slice نماینده. taskهای یکسان برای locate API، trace caller، affected tests و refresh بعد تغییر اجرا و با source تطبیق داده می‌شوند. setup effort، latency، freshness و token فقط اگر قابل اندازه‌گیری باشند ثبت می‌شوند. | تعیین بعد benchmark | TBD | TBD | پس از vertical slice | correctness مقابل source؛ مقایسه با native search؛ حداکثر یک نصب اولیه در صورت سود concrete | اکنون codebase نماینده‌ای برای benchmark وجود ندارد |
| Bounded product research | project-local `bounded-product-research` + Python stdlib pinned transport | transitive `httpx2 2.16.0` custom transport؛ broad crawler/browser framework | stdlib موجود امکان اتصال مستقیم به IP validate‌شده با TLS hostname اصلی را بدون dependency تازه می‌دهد. skill فقط policy/fetch/extract/provenance/job lifecycle را پوشش می‌دهد. workspace tests pin target IP، Host، redirect/private/IPv6، decoded size و deadline را می‌سنجند؛ هیچ performance claim اندازه‌گیری‌نشده‌ای پذیرفته نشد. | Python `3.12.x`; skill repository-local Phase 9 | `.agents/skills/bounded-product-research`; `backend/analysis/research/` | Python PSF؛ Project source | Phase 9 / Milestone B | `quick_validate.py` در `uv run` → valid؛ focused PostgreSQL/unit suite | browser fleet، queue و broad crawler رد؛ live sources تا permission/terms clarification disabled |

## منابع رسمی و upstream

- Spec Kit: <https://github.com/github/spec-kit> و <https://github.github.com/spec-kit/integrations/codex.html>
- Superpowers: <https://github.com/obra/superpowers>
- Grill Me: <https://github.com/mattpocock/skills>
- Frontend candidate: <https://github.com/vercel-labs/agent-skills>
- Browser candidate: <https://github.com/microsoft/playwright-mcp>
- OpenAI pricing/token accounting (rechecked 2026-11-14): <https://developers.openai.com/api/docs/pricing>,
  <https://developers.openai.com/api/docs/models/gpt-6-luna>,
  <https://developers.openai.com/api/docs/guides/token-counting>

## Phase 5.1 AI accounting and review evidence

| Need | Selected tool/skill | Alternatives | Evidence | Version | Install phase | Verification | Reason for deferral |
|---|---|---|---|---|---|---|---|
| Complete request estimate | project-owned `analysis.ai.pricing` | local tokenizer؛ paid input-token preflight | official token-counting docs say schema/framing count and local tokenizers are not exact. UTF-8 byte upper-bound + 15%/256-token margin, output bound and all attempts use the current official standard price. | `gpt-6-luna` price checked 2026-11-14 | Phase 5.1 | focused pricing/ledger tests؛ observed usage is not clipped؛ settlement idempotent | exact token-count endpoint deferred because it adds a network/billable preflight and does not guarantee invoice cap |
| Human semantic review | atomic synthetic JSON checkpoint + project assess/resume commands | keyword blacklist؛ LLM judge | valid IDs cannot prove Persian entailment. v1.2 separates structural/latency/spend/product-cost/human gates and preserves partial evidence without raw transport. | `PDA-AI-EVAL-v1.2` | Phase 5.3 | checkpoint/recovery/rejection tests; live artifact not generated because gates remain unset | real live output and completed human ratings remain `T039` |

## Phase 5.2 Iran-provider inventory

| Need | Selected tool/skill | Alternatives | Evidence | Version | Install phase | Verification | Reason for deferral |
|---|---|---|---|---|---|---|---|
| Iran-hosted AI API | AvalAI Responses API through existing OpenAI Python SDK | Liara AI | AvalAI itself documents `/v1/responses`, `gpt-5.6-luna`, response schema, model tariff, request ID and User API. Liara's checked model disables Structured Outputs and its base AI plan exceeds the no-purchase authority. Upstream authorization and Persian quality are not inferred. | AvalAI docs/model snapshot checked 2026-11-14؛ SDK lock `openai==3.49.0` | Phase 5.2; no new package | stub adapter/factory/eval tests; live pending | production activation deferred for provider clarification, local credential and eligible credit |
| AI cost conversion | project-owned `analysis.ai.avalai_pricing` + AvalAI `/user/v1/credit` | static/manual FX؛ provider dashboard only | model tariff `$5/$0.5/$30` per 1M tokens; current IRT-per-UNIT comes from provider, then 15% conservative margin. Product toman fields are not reused. | contract snapshot 2026-11-14 | Phase 5.2 | unit preflight and retry-inclusive cap tests | invoice reconciliation requires a real transaction/request ID |
| Direct OpenAI | none; adapter remains disabled | custom base URL | confirmed Iran deployment is not approved; a base URL change does not establish the direct contract | n/a | deferred | factory fail-closed test | unsupported deployment eligibility |

No package, subscription, account, credit or infrastructure was installed/provisioned in Phase 5.2. AvalAI reuses the
already locked Apache-2.0 OpenAI Python SDK only because AvalAI documents that SDK and its Responses endpoint directly.

license کامل Playwright که skill آن در repository نگهداری می‌شود در `third_party/licenses/playwright-Apache-2.0.txt`
ثبت شده است. license packageهای npm داخل packageهای قفل‌شده قابل بازرسی است. snapshotهای Vercel به‌علت نبود متن
مجوز قابل اتکا در revision دقیق، inactive هستند و استفادهٔ تازه یا redistribution آن‌ها مجاز فرض نمی‌شود.

## انتخاب‌ها و شواهد Phase 3

| Need | Selected tool/skill | Alternatives | Evidence | Version | Install phase | Verification | Reason for deferral |
|---|---|---|---|---|---|---|---|
| Python dependency management | uv project + universal lock | pip/requirements، Poetry | `uv lock` و نصب frozen داخل image؛ نصب محلی تازه به‌علت timeout میزبان wheel macOS کامل نشد، ولی cache-backed env و image imports موفق‌اند | uv `0.13.0` | M1 | `docker compose build api` موفق | — |
| Backend framework | Django + DRF | FastAPI؛ Django Ninja | هم‌راستا با plan/session/ORM؛ release metadata و index availability بررسی شد؛ suite واقعی workspace  PostgreSQL را استفاده می‌کند | Django `5.2.16`; DRF `3.17.1` | M1 | Django check، migration و API suite | — |
| PostgreSQL driver | psycopg binary extra | psycopg source؛ async driver | adapter رسمی psycopg و wheel Linux داخل image؛ lock exact | `3.3.6` | M1 | migration و concurrency suite | — |
| Development database | PostgreSQL container | SQLite؛ PostgreSQL host install | SQLite برای claimهای row lock/race رد شد؛ testها و migration روی container واقعی اجرا شدند | `18.1-alpine` | M1 | healthcheck، empty-db migration، barrier tests | production topology تا M4 deferred |
| Runtime server dependency | gunicorn | development runserver؛ ASGI server | dependency کوچک WSGI برای image pin شد؛ Compose فعلی عمداً runserver توسعه است | `23.0.0` | M1 | import و frozen image install | production invocation/hardening تا M4 |
| OpenAPI parsing در test | PyYAML | parser custom | contract 3.1 parse و route/example parity؛ فقط dependency گروه dev | `6.0.3` | M1 | contract tests | — |

نسخه‌های exact در `pyproject.toml` و `uv.lock` ثبت‌اند. proposalهای plan (`Django 5.2.17`, `DRF 3.18.1`) به نسخهٔ
واقعاً available/compatible بالا تغییر کردند؛ این تغییر evidence نصب و test دارد.

## انتخاب‌ها و شواهد Phase 4

| Need | Selected tool/skill | Alternatives | Evidence | Version | Install phase | Verification | Reason for deferral |
|---|---|---|---|---|---|---|---|
| UI runtime/build | React + React DOM + TypeScript + Vite React plugin | Next.js/SSR؛ Django template | static client با API مصوب؛ lock exact و build واقعی؛ هیچ Vercel/Node production requirement اضافه نشد | React/DOM `19.3.1`; TypeScript `5.9.3`; Vite `8.3.8`; plugin-react `6.3.0` | M2 | `npm ci`, typecheck, lint, build | production gateway تا M4 |
| Component tests | Vitest + Testing Library + jsdom | Jest؛ browser-only assertions | هفت behavioral test روی component و flow helper؛ jsdom جدیدتر به Node 22 نیاز داشت و `26.1.0` سازگار انتخاب شد | Vitest `4.1.12`; RTL `16.3.3`; user-event `14.6.10`; jest-dom `6.9.1`; jsdom `26.1.0` | M2 | `7 passed` | — |
| Browser/a11y | Playwright Test + axe integration | MCP؛ screenshot-only | شش test شامل seed و پنج journey واقعی؛ screenshot صرفاً evidence بصری است. نسخه axe جدید به Node 22 نیاز داشت، بنابراین آخرین نسخهٔ سازگار انتخاب شد | `@playwright/test 1.65.1`; `@axe-core/playwright 4.11.1` | M2 | `6 passed (57.0s)`؛ viewport 390/1440، overflow و keyboard | MCP بدون نیاز deferred |
| Persian font | self-hosted Vazirmatn variable از Fontsource | system font؛ CDN | package lock‌شده، asset در build محلی و license همراه package | `@fontsource-variable/vazirmatn 5.3.0` | M2 | سه WOFF2 در production build | OFL-1.1 |
| Focused lint | ESLint flat config + typescript-eslint + React hooks/refresh | broad preset؛ formatter جدید | ruleهای TypeScript/React بدون framework اضافی؛ false-positive نام fixture Playwright با override محدود شد | ESLint `10.15.0`; typescript-eslint `8.72.2`; hooks `7.1.1`; refresh `0.5.7` | M2 | صفر error/warning | — |

code-intelligence در Phase 4 نصب نشد. vertical slice اکنون موجود است، اما benchmark حداکثر دو candidate همچنان
یک ارزیابی جدا با taskهای یکسان و native `rg` است. live-AI pending است؛ deployment tooling در Phase 6 trigger و فقط
برای بسته‌بندی/rehearsal محلی استفاده شد.

## Phase 7 design and source-planning inventory

| Need | Selected tool/skill | Alternatives | Evidence | Version/commit | Install phase | Verification | Reason for deferral |
|---|---|---|---|---|---|---|---|
| Choice Desk visual direction | Anthropic `frontend-design` project-local + project RTL overlay | Anthropic `web-artifacts-builder`؛ inactive Vercel snapshots | official skill is docs-only and Apache-2.0; artifact builder carries React 18/Parcel/Tailwind/shadcn stack overlap. No maintainer performance claim was treated as measured quality. | `1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064`; SHA256 `SKILL.md=d91970639e9f5c37682ac7ab60094d35f1c7c1f38d731bd56396563aee10c1d3` | Phase 7 planning | frontmatter parsed، license file present، project path installed؛ current-turn skill catalog predates install, so native catalog discovery is pending next session | actual UI influence/browser quality waits for Milestone C implementation |
| Source feasibility | bounded `curl` probes + official pages; no crawler installed | browser fleet، scraping service، OpenAI built-in web search as market source | robots/page response measured for limited domains and separately recorded from indexed documentation; Digikala/Torob timeout and sports extraction gap remain explicit | observations 2026-11-15 | Phase 7 planning only | status/content-type/bytes for successful probes in `source-feasibility.md`; no corpus or large crawl | fetch/extractor dependencies wait for approved allowlist and Milestone B |
| New AI runtime direction | no package installed; plan direct OpenAI Responses using existing seam | AvalAI legacy adapter، generic multi-provider framework، self-hosted model | official Responses/streaming/vision/data/key/pricing/regions docs; Iran unsupported gate remains. No live call or Persian quality measurement. | exact model/provider SDK revalidation deferred | Milestone D | documentation/contract only؛ call count zero | install/activation deferred until model capability, license, region and explicit spend gates |

Installed files are `.agents/skills/frontend-design/SKILL.md` and `LICENSE.txt`; upstream license is Apache-2.0. The
project overlay forbids introducing Next.js, Tailwind/shadcn or Vercel deployment requirements merely from design guidance.

## Phase 8 Milestone A inventory

| Need | Selected tool/skill | Alternatives | Evidence | Version/commit | Install phase | Verification | Reason for deferral |
|---|---|---|---|---|---|---|---|
| Image decode/sanitize | Pillow | browser MIME، ImageMagick subprocess، custom parser | Pillow decodes JPEG/PNG/WebP, exposes dimension/frame checks and supports decode/re-encode without retaining EXIF/XMP. Official project declares MIT-CMU and Python ≥3.11; no performance claim is treated as workspace evidence. | `13.0.0` | Phase 8 / T049 | locked dependency plus invalid-bytes, metadata, ownership, limit and cleanup tests | OCR/vision intentionally deferred; no provider call |
| Fixture operation execution | Python bounded executor + PostgreSQL claim/lease | unbounded thread، Celery/Redis، WebSocket service | standard-library executor adds no service; PostgreSQL remains shared truth. It is explicitly non-durable: stale leases become `INTERRUPTED`, never silently restart. | Python 3.12 stdlib; repository implementation | Phase 8 / T009 | concurrency, cancellation, reconnect and proxy-first-chunk checks | durable queue deferred until measured need |
| Repeatable Linux browser check | existing Playwright Test/axe packages in official Playwright image | host Chrome channel؛ MCP | official image matches the locked runner, contains browser/system dependencies and avoids the unsupported host Node/macOS combination. It is test-only and does not enter runtime images. | Playwright `1.65.1`, image digest `sha256:1507cbfc550a63a6b7396791ca4f00df17beb56342d2447b3f106c306f525579` | Phase 8 verification | proxy journey at 390/1440, keyboard/reduced-motion/axe/screenshots | MCP still unnecessary |

`frontend-design` is natively discoverable in the Phase 8 skill catalog and was invoked as an installed project skill;
this differs from Phase 7, when only its files had been inspected after the catalog snapshot was created.
