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
| AI implementation | `purchase-ai-analysis` + OpenAI Python SDK | Google GenAI SDK؛ skillهای provider-specific | skill بومی، contract ساخت‌یافته، evidence/unknown، مرز scoring قطعی، failure/cost و evaluation را بدون framework اضافی پوشش می‌دهد. مقایسهٔ رسمی دو provider، OpenAI `gpt-6-luna` را به‌صورت مشروط برای deployment و کاربرانِ منطقهٔ پشتیبانی‌شده انتخاب کرد؛ کیفیت فارسی و latency هنوز اندازه‌گیری نشده‌اند. | skill repository-local Phase 5؛ مدل `gpt-6-luna`؛ SDK `3.49.0` | `.agents/skills/purchase-ai-analysis`; dependency project-scoped | Project source؛ SDK Apache-2.0 | Phase 5 M3 | هر دو skill valid؛ AI suite `21 passed`، backend `84 passed`، SDK signature compatible؛ live calls `0` | live evaluation تا تعیین region، credential محلی و سقف بودجهٔ صریح deferred است |
| Deployment | guidance متمرکز Docker/deployment | platform-specific deployment skills | trigger: پیش از production/deployment work. production config، secrets، health، persistence، backup/restore، migrations و rollback پوشش داده می‌شود. | تعیین در زمان ارزیابی | TBD | TBD | پیش از deployment | compose/config validation و restore/rollback rehearsal متناسب با فاز | deployment در Phase 0 مجاز نیست |
| Code intelligence | هیچ ابزار اولیه نصب نشده؛ بعداً حداکثر دو گزینه از Graphify، codebase-memory-mcp، Serena و GitNexus مقایسه می‌شوند | native `rg`, Git و language tooling | trigger: پس از vertical slice نماینده. taskهای یکسان برای locate API، trace caller، affected tests و refresh بعد تغییر اجرا و با source تطبیق داده می‌شوند. setup effort، latency، freshness و token فقط اگر قابل اندازه‌گیری باشند ثبت می‌شوند. | تعیین بعد benchmark | TBD | TBD | پس از vertical slice | correctness مقابل source؛ مقایسه با native search؛ حداکثر یک نصب اولیه در صورت سود concrete | اکنون codebase نماینده‌ای برای benchmark وجود ندارد |

## منابع رسمی و upstream

- Spec Kit: <https://github.com/github/spec-kit> و <https://github.github.com/spec-kit/integrations/codex.html>
- Superpowers: <https://github.com/obra/superpowers>
- Grill Me: <https://github.com/mattpocock/skills>
- Frontend candidate: <https://github.com/vercel-labs/agent-skills>
- Browser candidate: <https://github.com/microsoft/playwright-mcp>

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
یک ارزیابی جدا با taskهای یکسان و native `rg` است. live-AI و deployment tooling نیز تا trigger M3/M4 deferred ماندند.
