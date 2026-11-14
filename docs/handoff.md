# تحویل Phase 5 — M3 adapter واقعی AI؛ ارزیابی live pending

**تاریخ اجرا:** ۱۴ نوامبر ۲۰۲۶  
**وضعیت دقیق:** M3 adapter implemented — live evaluation pending  
**مرز:** M1/M2 پذیرفته‌اند؛ M4 و production deployment اجرا نشده‌اند. بازبینی بصری product lead خارجی همچنان
pending است و screenshotهای محلی به‌عنوان بازبینی خارجی گزارش نمی‌شوند.

## 1. Spec Kit و taskهای اجراشده

- artifactهای canonical، constitution، tooling، handoff قبلی و implementation موجود خوانده شدند. taskهای واقعی M3
  عبارت‌اند از `T038`, `T039`, `T040`.
- `$speckit-analyze` پس از اصلاح plan/spec/research اجرا شد: ۳۶ functional requirement، ۸ success criterion، ۴۳
  task؛ conflict بحرانی یا constitution violation پیدا نشد. دو gap رفع شد: مدل دادهٔ budget/circuit و متن قدیمی
  authorization در tasks. checklistها 30/30 و 25/25 کامل بودند.
- `$speckit-implement` فقط به M3 محدود شد. `T038` و `T040` کامل‌اند. test/harness بخش `T039` ساخته و سبز است، اما
  خود task برای نبود evidence واقعی live باز می‌ماند. `T041–T043` بدون تغییر unchecked هستند.
- `purchase-ai-analysis` پیش از implementation ساخته و با validator رسمی skill تأیید شد. framework عامل عمومی،
  vector DB، Redis/Celery یا code-intelligence نصب نشد.

## 2. اصلاح provenance و مجوز Vercel

revision دقیق `vercel-labs/agent-skills` برابر `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` دوباره بررسی شد.
tree آن هیچ `LICENSE`، `NOTICE` یا `COPYING` در root یا مسیر دو skill نداشت. metadata عبارت `license: MIT` در یکی
از skillها متن grant/notice کامل نیست و skill دیگر declaration مجوز هم ندارد. بنابراین گزارش قبلی MIT اصلاح شد:

- snapshotهای `react-best-practices` و `web-design-guidelines` فقط برای provenance نگه داشته و inactive شدند؛
  invoke، اتکای تازه یا redistribution آن‌ها مجاز فرض نمی‌شود.
- راهنمای project-owned در `purchase-regret-project` بر requirements خود پروژه و منابع رسمی React/Vite/WAI متکی است؛
  Next.js، Vercel deployment، SSR/RSC وارد پروژه نشده‌اند.
- evidence و وضعیت در `docs/tooling.md` و `research.md` ثبت شده است؛ notice قابل اعمال دیگری در revision یافت نشد.

## 3. انتخاب provider/model

حداکثر دو گزینه با اسناد و pricing رسمی مقایسه شدند:

| معیار | OpenAI `gpt-6-luna` | Google `gemini-3.5-flash-lite` |
|---|---|---|
| structured output | مستند | مستند |
| قیمت list / 1M token | input `$0.10`، output `$0.50` | input `$0.30`، output `$2.50` |
| کنترل داده | `store=false` برای application state؛ API data به‌طور پیش‌فرض training نیست | paid tier برای improve products استفاده نمی‌شود |
| Persian/latency | capability چندزبانه مستند؛ در workspace اندازه‌گیری نشده | capability مستند؛ در workspace اندازه‌گیری نشده |
| region | فقط فهرست رسمی؛ ایران در فهرست نیست | فقط available regions؛ ایران در فهرست نیست |

انتخاب مشروط OpenAI Responses API، مدل `gpt-6-luna` و SDK رسمی Python `3.49.0` است: contract-compatible و با
list cost کمتر. مدل snapshot جداگانه‌ای در catalog رسمی فعلی ندارد؛ این محدودیت ثبت شده است. deployment/user region
واقعی هنوز اعلام نشده، پس recommendation به معنی مجوز activation نیست.

## 4. adapter، مرز ایمنی و کنترل هزینه

- request `PDA-EXPLAIN-v1` شامل target label به‌عنوان دادهٔ untrusted، outcome/dimension/rule/unknown/action قطعی و
  evidence نرمال است. prompt `PDA-EXPLAIN-P1` و model صریح‌اند؛ credentials فقط backend environment هستند.
- response strict JSON، outcome echo، exact unknown acknowledgement، headline و حداکثر سه claim دارد. mapping
  claim/evidence/rule و lengthها validate می‌شوند. وجود evidence ID تضمین semantic entailment متن آزاد نیست؛ review
  انسانی/evaluation برای آن لازم است.
- AI فقط توضیح فارسی، اولویت concerns و actions مبتنی بر داده را می‌سازد. outcome، محاسبه budget، dimensionها،
  unknownها و publication authority کاملاً از engine می‌آیند. mock=`MOCK_ASSISTED`، موفق live=`AI_ASSISTED_SUCCESS`
  و هر failure/unsupported=`RULE_BASED_LIMITED` است.
- input حداکثر ۸۱۹۲ UTF-8 byte به‌عنوان token upper bound محافظه‌کار، output حداکثر ۵۱۲ token، timeout هشت ثانیه و
  حداکثر دو attempt است. فقط connection/timeout/408/409/429/5xx retry می‌شوند؛ مدل گران‌تر fallback نمی‌شود.
- PostgreSQL با row lock، worst-case `$0.002152` برای دو attempt هر generation را رزرو می‌کند. limit پیش‌فرض ۱۰
  generation/guest/day، deployment budget `$1/day` و circuit پنج failure/پنج دقیقه است. call شبکه بیرون transaction
  است و revision/operation-token/epoch/expiry پیش از publish دوباره کنترل می‌شوند.
- metadata مجاز: provider/model/version، token usage، latency، attempts، status/error class و estimate هزینه. raw
  answer/label/prompt/response، session secret و exception text persist/log نمی‌شوند. metadata guest-linked پس از ۹۰
  روز cleanup می‌شود. invoice provider مرجع نهایی است.

## 5. آزمون‌ها و verification اجراشده

TDD: ابتدا سه module جدید به‌علت نبود `openai_adapter` و `evaluation` با ۳ import error قرمز شدند؛ پس از implementation
سبز شدند. پوشش adapter شامل structured success، malformed/incomplete، claim نامجاز، outcome/unknown متناقض، متن
prompt-injection در label/answer، timeout/rate/transient، exhaustion، credential، quota/budget/circuit، mock/live و
clear/delete/expiry هنگام call مسدود provider است.

| فرمان/بررسی | نتیجه |
|---|---|
| `uv lock` و `uv sync --frozen` | موفق؛ OpenAI `3.49.0` و ۲۲ package runtime frozen |
| SDK signature inspection بدون network | `responses.create` با parameterهای لازم compatible |
| AI suite | ۲۱ test، پاس |
| backend suite روی PostgreSQL | ۸۴ test، پاس |
| Django check / migration drift | issue صفر / `No changes detected` |
| skill validation | `purchase-ai-analysis` و `purchase-regret-project`: valid |
| frontend typecheck / lint | موفق؛ صفر error/warning |
| component tests | ۳ file، ۷ test، پاس |
| Vite production build | موفق؛ JS `250.84 kB`، CSS `12.29 kB` |
| Docker image + migration | build موفق؛ `analysis.0002_ai_live_controls` اعمال شد؛ API/DB healthy |
| Playwright Chrome/PostgreSQL | ۶ test، پاس در حدود ۱.۵ دقیقه |

## 6. live evaluation و هزینهٔ واقعی

live evaluation اجرا نشد. gate check داخل container بدون نمایش مقدار secret:

```text
OPENAI_API_KEY=UNSET
BEFOREBUY_AI_SUPPORTED_REGION_CONFIRMED=UNSET
BEFOREBUY_LIVE_EVAL_BUDGET_USD=UNSET
persisted_live_invocations=0
```

بنابراین تعداد call واقعی `0`، attempt واقعی `0` و هزینهٔ واقعی/estimate run برابر `$0.00` است. هیچ output mock به‌عنوان
live گزارش نمی‌شود. dataset `PDA-AI-EVAL-v1`، thresholdهای از پیش ثابت و command cap-aware آماده‌اند، اما quality
فارسی، latency، actionability و added usefulness مدل هنوز measured نیستند.

## 7. مقایسه با baseline قطعی

baseline فعلی template/mock، نتیجهٔ قطعی و safe fallback را بدون network می‌دهد. adapter می‌تواند intended use و
urgency را به توضیح فارسی طبیعی‌تر وصل کند و حداکثر سه concern/action را اولویت دهد، ولی حق افزودن fact محصول یا
تغییر نتیجه ندارد. چون live run انجام نشده، هیچ evidence برای بهترشدن readability/actionability/usefulness نسبت به
baseline وجود ندارد. حتی عبور مجموعهٔ شش‌موردی نیز evidence کاهش purchase regret نخواهد بود.

## 8. راه‌اندازی محلی بدون secret

```bash
cp .env.example .env
docker compose build api
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up -d --wait

cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

حالت عادی `BEFOREBUY_AI_MODE=mock` است. برای محیطی که backend و کاربران آن رسماً supported هستند، فقط در `.env`
محلی backend مقدار `BEFOREBUY_AI_MODE=live`، تأیید region و `OPENAI_API_KEY` تنظیم می‌شود؛ key هرگز در chat، Git یا
متغیر Vite قرار نمی‌گیرد. ارزیابی علاوه بر این‌ها به `BEFOREBUY_LIVE_EVAL_BUDGET_USD=<explicit-cap>` نیاز دارد:

```bash
docker compose run --rm api python backend/manage.py evaluate_live_ai
```

## 9. gateهای باقی‌مانده

1. اعلام محل واقعی backend و کاربران و تطبیق با region رسمی provider.
2. تنظیم credential فقط در backend secret environment و تعیین cap دلاری صریح evaluation توسط مالک بودجه.
3. اجرای شش case live تا cap، ثبت call/attempt/token/latency/estimate و review انسانی مستقل readability، evidence،
   actionability و added usefulness؛ thresholdها پس از دیدن نتیجه بی‌صدا پایین آورده نمی‌شوند.
4. بازبینی بصری خارجی product lead برای M2 همچنان pending است.
5. `T039` تا evidence واقعی باز می‌ماند؛ سپس readiness M3 می‌تواند دوباره ارزیابی شود.
6. M4: production gateway/hardening، TLS/infrastructure، backup/restore، migration/rollback rehearsal و deployment؛
   هیچ‌یک در این فاز اجرا نشده‌اند.

## 10. task و archive

- complete: `T038`, `T040`.
- pending live evidence: `T039`.
- untouched/unchecked M4: `T041`, `T042`, `T043`.
- handoff قبلی بدون تغییر محتوایی در `docs/archive/phase-4-handoff.md` آرشیو شد.

**M3 adapter implemented — live evaluation pending**
