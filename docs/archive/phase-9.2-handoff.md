# تحویل Phase 9.2 — پایلوت offer واقعی با مانع دسترسی منبع

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline:** `f7b57857e4f41669d3f25b73a9026615fb461809`  
**branch:** `002-personalized-shopping-copilot`  
**وضعیت:** `Real-source offer pilot partially complete — source blockers documented`  
**کامل:** `T060–T065`  
**partial:** `T066`  
**باز و بدون تغییر:** `T013`, `T018`, `T019`، همهٔ Milestoneهای C–E و هر دو feature-specific `T039`

## دامنه و workflow اجراشده

Spec Kit همان feature موجود `002-personalized-shopping-copilot` را مالک ماند. نیازمندی‌های `FR-055–FR-060`،
plan/data model/ranking/OpenAPI/source register و taskهای یکتای `T060–T066` اضافه شدند. `$speckit-analyze` پس از
تغییر substantive اجرا شد؛ ناسازگاری duplicated Technolife status و مرز offer-view در برابر product ranking اصلاح شد.
`$speckit-implement` فقط `T060–T066` را در scope داشت. native skill discovery جدا از خواندن instruction file انجام شد؛
مهارت‌های project/research/backend/frontend/Playwright، TDD، debugging، analyze/implement و verification استفاده شدند.

## سیاست منبع و نتیجهٔ ارزیابی

- **Torob:** `/search/` در robots ممنوع است؛ exact `/p/` منع صریح خودکار در material بررسی‌شده نداشت. terms می‌گوید
  دادهٔ فروشگاه‌ها را تجمیع و کاربر را به فروشگاه هدایت می‌کند، اما permission عمومی reuse نمی‌دهد. policy narrow فقط
  exact product، pace حداقل 2s، freshness 6h، raw حداکثر 24h و attribution است.
- **Digikala:** query/search paths بسته‌اند؛ path مشاهده‌شدهٔ `dkp-*` صراحتاً ممنوع نبود و terms استفادهٔ غیرتجاری با
  attribution را بیان می‌کند. HTML دقیق فقط routing shell و endpoint حدس‌زده‌شده 404 داد؛ به‌علت
  `TECHNICAL_EXTRACTION_FAILURE` خاموش است، نه ادعای منع حقوقی.
- **Technolife، Bkalaa، Takkalaban:** در material رسمی بررسی‌شده منع صریح مرتبط پیدا نشد؛ این absence permission نیست.
  فقط دو product ID بررسی‌شدهٔ Technolife و exact `/product/` دو merchant دیگر قابل فعال‌سازی‌اند. واحد مبهم fail closed
  می‌شود.
- Apple/adidas/Decathlon و همهٔ search/account/cart pathها همچنان خاموش‌اند. هیچ CAPTCHA/login/paywall دور زده نشد و
  هیچ provider message ارسال نشد.

## پیاده‌سازی

- migrationهای `0008`/`0009` original amount/currency، `price_toman`، mandatory charge، merchant URL، observation kind
  و source role مقایسه‌گر را اضافه کردند. IRR فقط با `10 IRR = 1 TOMAN` تبدیل می‌شود؛ shipping/fee نامعلوم صفر نیست.
- adapter registry موجود گسترش یافت: JSON-LD merchant offer و source-specific Torob `__NEXT_DATA__`. missing structure،
  invalid unit، price conflict و layout drift failure صریح‌اند. Torob merchant redirectها فقط نمایش داده می‌شوند و خودکار
  follow نمی‌شوند.
- publication pipeline موجود چند offer را اتمیک ذخیره می‌کند. cache clone همهٔ provenance جدید را حفظ می‌کند. API view
  deterministic بر `price_toman` مرتب، same variant/seller/price را با ترجیح merchant verification deduplicate می‌کند؛
  raw observation/discrepancy در snapshot باقی می‌ماند.
- `configure_market_sources --enable|--disable` policyهای محدود را reproducible می‌سازد؛ default Compose همچنان
  `OFFLINE` است.
- `/copilot` ورودی ۱–۳ exact HTTPS URL، brief confirmation، progress، offer card، source/merchant link، freshness state،
  unknown total و failure coverage را نشان می‌دهد. copy فقط «کمترین قیمت بین منابع بررسی‌شده» است و ادعای ارزان‌ترین
  ایران/قیمت تحویلی ندارد. LIVE/CACHE/STALE/CAPTURED_FIXTURE/SYNTHETIC از هم جدا هستند.

## پایلوت زنده و accounting

پنج محصول در سه دسته از API واقعی NGINX اجرا شدند:

| محصول | منبع | نتیجه | request | offer زنده |
|---|---|---|---:|---:|
| Philips NA230 | Technolife + Bkalaa + Takkalaban | path اولیه Technolife؛ سپس Bkalaa DNS و Takkalaban transport failure | 2 | 0 |
| Samsung Q60D 55 | Torob | `TRANSPORT_ERROR` | 1 | 0 |
| Pakshoma TFB-95401 | Torob | `TRANSPORT_ERROR` | 1 | 0 |
| Tokyo 52cc chainsaw | Torob | `TRANSPORT_ERROR` | 1 | 0 |
| Nokia 105 2024 | Technolife | path اولیه پیش از request رد شد | 0 | 0 |

پس از narrow کردن Technolife به product IDها، NA230 به transport رسید ولی timeout شد (۱ request). اجرای browser واقعی
Torob نیز failure را در UI نشان داد (۱ request). اتصال pinned و proxy-free این workspace به Torob/Technolife/Takkalaban
timeout و DNS Bkalaa fail شد؛ proxy یا تضعیف SSRF استفاده نشد. این نتیجه permanent unavailability نیست.

کل controlled outbound مصرف‌شده **29/100** است: 19 feasibility/policy، 7 persisted live-pipeline و 3 diagnostic.
browser-assisted primary-source lookup چون count داخلی قابل‌اندازه‌گیری نیست جدا گزارش شده است. retry، AI/provider call،
account، خرید و paid API صفر بودند.

captured bodies قبلی adapter را با دادهٔ factual حداقلی ثابت کردند، نه live pipeline: Torob Q60D شش seller با بازهٔ
`109,600,000–115,890,000` تومان؛ Bkalaa NA230 برابر `24,466,434 IRT`؛ Takkalaban NA230 برابر
`239,900,000 IRR = 23,990,000` تومان. Technolife visible NA230 برابر 22,400,000 تومان دیده شد ولی به‌علت conflict
JSON-LD/visible unit به‌عنوان extracted offer منتشر نشد. هدف سه offer live و repeat منبع موفق محقق نشد؛ `T066` partial است.

## verification

- RED ثبت‌شده: سه failure adapter (original currency، IRR conversion، Torob multi-offer) پیش از implementation.
- focused backend پس از identity correction: 21/21؛ affected research/SSRF/concurrency/lifecycle قبلی: 38/38.
- canonical PostgreSQL backend: **234 discovered/run، 234 passed، 0 skipped/failed/error** در 40.765s.
- frontend Vitest: **16/16 passed**؛ TypeScript و ESLint موفق.
- Playwright روی NGINX: feature copilot **4/4 passed**؛ اجرای broader 14-test collection برابر 9 passed، 3 skipped و دو
  failure نامرتبط/پیکربندی‌شده بود (`m2` context hard-coded 5173 و production HTTPS smoke روی dev HTTP). این دو به Phase
  9.2 نسبت داده نمی‌شوند و به‌عنوان pass گزارش نشده‌اند.
- screenshot regression captured offer:
  `artifacts/screenshots/copilot-phase9-2-captured-offer-mobile.png` (runtime artifact، خارج Git).
- screenshot اجرای LIVE failure:
  `artifacts/screenshots/copilot-phase9-2-live-failure-desktop.png` (runtime artifact، خارج Git).
- migrationها روی volume توسعه بدون reset اعمال و سه service healthy شدند. هیچ volume/database حذف نشد.

## فرمان‌های reproducible

```sh
docker compose exec api python backend/manage.py migrate --noinput
docker compose exec api python backend/manage.py configure_market_sources --enable
BEFOREBUY_RESEARCH_MODE=LIVE docker compose up --build -d api web
```

سپس `http://127.0.0.1:58080/copilot`، ساخت conversation، تکمیل/تأیید brief، ورود ۱–۳ exact URL و «بررسی پیشنهادها».

بازگشت به حالت امن:

```sh
docker compose exec api python backend/manage.py configure_market_sources --disable
docker compose up -d --force-recreate api
```

تست‌ها:

```sh
./scripts/test-backend.sh --keepdb --verbosity 1
cd frontend && npm test -- --run && npm run typecheck && npm run lint
PLAYWRIGHT_BASE_URL=http://127.0.0.1:58080 NODE_PATH="$PWD/node_modules" npm run test:e2e -- ../tests/e2e/copilot-milestone-a.spec.ts
```

## gateهای باقی‌مانده

1. اجرای همین pilot از شبکه‌ای با direct pinned access (ترجیحاً deployment ایران) و ثبت حداقل یک source موفق؛ سپس repeat
   محدود همان source و هدف سه merchant live.
2. clarification حقوقی/retention/reuse برای Torob و merchantها؛ narrow pilot blanket permission نیست.
3. parser اختصاصی Technolife فقط پس از حل تعارض واحد با evidence صریح؛ magnitude inference ممنوع است.
4. sports source/fixture معتبر برای `T018/T019`، full Choice Desk/ranking، memory، AI و public deployment مجوز مستقل دارند.
5. feature 001 `T039` و feature 002 `T039` همچنان pending هستند.

حذف نامرتبط `test.txt` حفظ و از commit خارج می‌شود. secret، raw page، cookie، DB، log، screenshot/runtime artifact وارد Git
نمی‌شود.

**Real-source offer pilot partially complete — source blockers documented**
