# تحویل Phase 4 — M2 رابط فارسی/RTL

**تاریخ اجرا:** ۱۴ نوامبر ۲۰۲۶  
**وضعیت:** M2 interface implemented and browser-verified؛ محصول کامل و production-ready نیست.

## Spec Kit و مرز اجرا

1. artifactهای feature canonical و taskهای واقعی خوانده شدند. شناسه‌های M2 عبارت‌اند از `T026`, `T027`,
   `T030`, `T033`, `T034`؛ فقط همین پنج مورد complete شده‌اند.
2. قواعد نمایش follow-up در `questionnaire.md` قطعی شد: `F-001` فقط برای repair جدی/تناقض، `F-002` فقط برای
   پاسخ نامعلوم `Q-002`، و `F-003` برای gaming/accessibility/work-study؛ سقف کل سه مورد و ترتیب ثابت است.
   مقدار نامعلوم `Q-004` به‌تنهایی follow-up نمی‌سازد. contract عمومی API گسترش نیافت.
3. `$speckit-analyze` پس از اصلاح artifactها اجرا شد: ۴۴ requirement قابل ساخت، ۴۳ task، پوشش ۱۰۰٪، critical
   conflict صفر و constitution violation صفر. checklistهای requirements و technical plan به‌ترتیب ۳۰/۳۰ و
   ۲۵/۲۵ بودند.
4. `$speckit-implement` فقط روی M2 اجرا شد. `T038–T040` (M3) و `T041–T043` (M4) همچنان unchecked و
   unimplemented هستند. full-feature convergence اجرا نشد.

## مهارت‌ها و انتخاب ابزار

- `purchase-regret-project` برای مرز فاز و تصمیم‌های محصول؛ overlay مربوط به M2 به reference آن افزوده شد.
- `speckit-analyze` و `speckit-implement` برای workflow اصلی؛ `test-driven-development`،
  `systematic-debugging` و `verification-before-completion` برای implementation و evidence.
- `react-best-practices` و `web-design-guidelines` از `vercel-labs/agent-skills`، repository revision
  `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` و skill version `1.0.0`. guideline پویا در revision
  `434b7f91364665f2f733b310ec54809bf8f37937` خوانده شد. استفاده فقط به React/TypeScript/Vite و accessibility
  محدود است؛ Next.js، SSR، RSC، Vercel deployment یا سرویس دیگری وارد نشد. این upstream در revision انتخاب‌شده
  فایل license و GitHub license metadata ندارد؛ بنابراین MIT ادعا نمی‌شود و بازتوزیع skill باید دوباره بررسی شود.
- skill رسمی `playwright-cli` از Microsoft Playwright `v1.65.1`، tag commit
  `bbd948344ea9a60bf1e6f125c02ca99b2b51593b`، Apache-2.0. notice کامل در
  `third_party/licenses/playwright-Apache-2.0.txt` است. CLI برای inspection تعاملی و Playwright Test برای
  آزمون تکرارپذیر استفاده شد؛ MCP قابلیت لازم اضافه‌ای نداشت و نصب/استفاده نشد.
- code-intelligence، live-AI و deployment tooling در M2 نصب نشدند.

## رابط و رفتارهای پیاده‌شده

- React + TypeScript + Vite در `frontend/` با lockfile exact، فونت self-hosted Vazirmatn، `dir=rtl`، skip link،
  focus واضح، landmarkهای معنایی و `<bdi>` برای رشته‌های Latin/Persian.
- نمای شروع با «خریدم را بررسی کن»، questionnaire مرحله‌ای با progress/back، دو فیلد محصول، شش پرسش اصلی و
  حداکثر سه follow-up قطعی.
- ورودی تومان با رقم فارسی/لاتین، تفکیک صریح صفر از نامعلوم، حفظ پاسخ‌ها پس از validation error و جلوگیری از
  submit تکراری. frontend engine مستقل scoring یا rule business جدید ندارد.
- report با نتیجه اصلی، چهار dimension مستقل، unknownهای مجاور نتیجه، evidence، اقدام بعدی، وضعیت model-fit،
  expiry، edit/reanalyse و feedback اختیاری ۱ تا ۵ با تغییر/حذف.
- copy جدا برای `MOCK_ASSISTED`، `RULE_BASED_LIMITED` و حالت live آینده؛ enum خام، score خرید، ادعای دقت،
  testimonial یا تأیید فنی ساختگی نشان داده نمی‌شود.
- history همان مرورگر با loading/error/empty، بازکردن، حذف تکی، clear همه، refresh/revisit و پیام عمومی برای
  analysis ناموجود/منقضی/حذف‌شده/غیرقابل‌دسترسی. UI ادعای حذف قطعی برای 404 نمی‌کند.
- sequence/abort guard جلوی بازگرداندن state قدیمی را می‌گیرد؛ conflict/stale revision قابل بازیابی است و feedback
  پس از revision/mode جدید carry نمی‌شود. draft یا پاسخ حساس در localStorage/sessionStorage ذخیره نمی‌شود.
- layout پاسخ‌گو در موبایل و desktop، بدون horizontal overflow، با long model name و متن فارسی طولانی.

## اتصال واقعی و correction متمرکز backend

Frontend از proxy هم‌origin `/api` به Django روی Docker و PostgreSQL استفاده می‌کند. bootstrap session، cookie و
CSRF header مرکزی‌اند؛ CSRF خاموش نشده، CORS باز نشده و API persistence با fixture یا browser storage جایگزین نشده است.

برای تست repeatable حالت limited، یک کنترل کاملاً test-only افزوده شد:

- `BEFOREBUY_E2E_TEST_CONTROLS` در sample و حالت پیش‌فرض `0` است.
- تنها وقتی این flag برابر `1` **و** header اختصاصی `X-BeforeBuy-E2E-Explanation: limited` وجود دارد، generator
  تزریقی failure می‌سازد و fallback واقعی `RULE_BASED_LIMITED` اجرا می‌شود.
- create/edit/reanalysis همان injection محدود را دریافت می‌کنند. public OpenAPI contract و shape پاسخ تغییر نکرد.
- دو regression backend ثابت می‌کنند header با flag خاموش بی‌اثر و با flag روشن limited است.

در debugging سه defect واقعی اصلاح شد: regex قبلی رقم فارسی را به‌اشتباه حرف می‌دید، report پیش از پایان refresh
history نمایش داده می‌شد و feedback فوری را drop می‌کرد، و `visibility:hidden` مانع focus واقعی skip link بود.
هر سه با component/browser evidence بسته شدند.

## نسخه‌های exact frontend

| جزء | نسخه |
|---|---:|
| Node.js / npm مشاهده‌شده | `20.19.0` / `10.8.2` |
| React / React DOM | `19.3.1` / `19.3.1` |
| TypeScript / Vite / React plugin | `5.9.3` / `8.3.8` / `6.3.0` |
| Vazirmatn variable | `5.3.0` |
| Vitest / Testing Library React / user-event | `4.1.12` / `16.3.3` / `14.6.10` |
| jest-dom / jsdom | `6.9.1` / `26.1.0` |
| ESLint / typescript-eslint | `10.15.0` / `8.72.2` |
| React hooks / refresh lint plugins | `7.1.1` / `0.5.7` |
| Playwright Test / axe Playwright | `1.65.1` / `4.11.1` |

`jsdom` و `axe` جدیدتر که Node 22 می‌خواستند انتخاب نشدند. Playwright bundled Chromium روی macOS 12 این میزبان
پشتیبانی نشد؛ config از channel رسمی Chrome نصب‌شده استفاده می‌کند.

## verification نهایی تازه

همهٔ نتیجه‌های زیر روی state نهایی repository و stack واقعی Docker اجرا شدند:

| Check | Result |
|---|---|
| frozen frontend install | `npm ci --ignore-scripts --no-audit --no-fund`؛ ۲۵۲ package، موفق |
| TypeScript | `npm run typecheck`؛ موفق |
| lint | `npm run lint`؛ صفر error/warning |
| component tests | ۳ file، ۷ test، همگی پاس در `5.45s` |
| production build | موفق در `420ms`؛ JS `250.84 kB`، CSS `12.29 kB`، سه WOFF2 |
| browser stack | API و PostgreSQL هر دو healthy؛ Chrome channel |
| Playwright | ۶ test، همگی پاس در `57.0s` |
| accessibility automation | axe serious/critical صفر در viewport موبایل و desktop |
| responsive assertions | horizontal overflow صفر در ۳۹۰ و ۱۴۴۰؛ keyboard skip/focus پاس |
| Django check | issue صفر |
| migration drift | `No changes detected` |
| PostgreSQL backend suite | ۶۲ test، همگی پاس در `3.589s` |

اولین تلاش verification نهایی به‌علت PATH shell، Node ناسازگار Hermes را انتخاب کرد و قبل از اجرای test متوقف شد؛
به‌عنوان evidence محصول شمرده نشد. اجرای گزارش‌شده بالا با Node exact `20.19.0` از NVM انجام شد. همچنین کشف شد
`manage.py test tests` از root پس از وجود `tests/e2e` label collision دارد؛ دستور canonical از working directory
`backend/` اجرا شد و فقط نتیجه ۶۲-test آن معتبر است.

پوشش browser شامل ده requirement در پنج journey و یک seed است: create/result، رقم فارسی/تومان، صفر در برابر
نامعلوم، cap follow-up، edit/reanalyse و feedback stale، refresh/history، delete/clear، isolation دو context، labelهای
mock/limited، و mobile/keyboard. testها data خود را می‌سازند و فقط همان داده را پاک می‌کنند؛ history توسعه‌دهنده
برای shortcut پاک نمی‌شود.

## تصاویر بازبینی‌شده

- `artifacts/screenshots/m2-mobile-390-report.png` — `390×2640`، report mock موبایل.
- `artifacts/screenshots/m2-desktop-1440-limited.png` — `1440×1590`، report limited desktop.

هر دو پس از آخرین browser run تولید و به‌صورت بصری بازبینی شدند. screenshot جای test یا claim کامل accessibility نیست.

## startup محلی

```bash
cp .env.example .env
docker compose build api
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up -d --wait

cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

URL رابط: `http://127.0.0.1:5173/`  
URL bootstrap API: `http://127.0.0.1:58000/api/v1/session`

فرمان‌های دقیق smoke cookie/CSRF و verification در `specs/001-purchase-decision-analysis/quickstart.md` و عملیات
backend در `docs/backend-operations.md` هستند. hostname `127.0.0.1` باید ثابت بماند.

## taskها، محدودیت‌ها و ادامه

- کامل: `T026`, `T027`, `T030`, `T033`, `T034`.
- باقی M3: `T038–T040` برای provider/model واقعی، budget و evaluation live AI.
- باقی M4: `T041–T043` برای production web gateway، hardening، backup/restore و rollback rehearsal.
- mode عادی فعلی mock است؛ معیار کیفیت AI زنده یا performance عمومی محسوب نمی‌شود.
- Compose توسعه از runserver استفاده می‌کند؛ TLS، production static serving و production deploy وجود ندارد.
- نصب تازهٔ dependency Python روی macOS همچنان unverified است؛ Docker مسیر تأییدشده backend است.
- Chrome channel میزبان لازم است؛ bundled Chromium روی host فعلی unavailable است.
- بازتوزیع skillهای Vercel تا روشن‌شدن license upstream نیازمند بازبینی است.
- code-intelligence benchmark، live provider و deployment tooling عمداً به trigger فازهای بعد deferred مانده‌اند.

handoff قبلی بدون تغییر در `docs/archive/phase-3-handoff.md` آرشیو شده است.

M2 interface implemented and browser-verified
