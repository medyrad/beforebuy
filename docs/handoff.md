# تحویل Phase 11 — تنظیمات دستیار و شناخت من

**Milestone D settings and opt-in memory implemented and verified;
OpenAI adapter stub-tested — live activation remains pending.**

تاریخ: 2026-11-15؛ branch: `002-personalized-shopping-copilot`؛ baseline:
`686a3e4d1135ff72e4c6a193c7b192e7895b0e94`. تماس provider/public source و هزینهٔ واقعی: **صفر**.
AI روی `mock` و research روی `OFFLINE` است؛ انتشار عمومی یا خرید انجام نشد.

## دامنه و workflow

T032–T041 feature002 تکمیل شدند. feature001 T039، T042–T048/T050 feature002، T066 و gateهای باز قبلی pending
هستند؛ full-product convergence و Milestone E ادعا نمی‌شوند. مهارت‌های موجود project، Spec Kit analyze/implement،
backend، AI، TDD/debugging، frontend، verification و Playwright استفاده شدند؛ subagent یا toolchain جدید نداریم.
Checklist برابر 16/16 و extension hook موجود نیست. Analyze محدود: ۱۵ FR و سه SC به ۱۰ task نگاشت شدند؛
پوشش دامنهٔ مجاز ۱۰۰٪، task نامرتبط و مانع بحرانی باز صفر. FR-035 اینجا فقط memory-only export است، نه T050.
handoff قبلی عیناً در `docs/archive/phase-10-handoff.md` حفظ و hash آن با baseline مقایسه شد.

## تجربهٔ قابل نمایش

در `http://127.0.0.1:58080/copilot`، بالای صفحه «تنظیمات دستیار» و «شناخت من» را باز کنید؛ `/` legacy است.
کلید password-style وارد، backend-side رمز و masked می‌شود؛ save/replace/delete هیچ درخواست بیرونی ندارد.
ورودی بعد از submit پاک می‌شود. unconfigured، stored/unvalidated، failed و blocked جدا هستند؛ validated برای آینده
تعریف شده و هیچ کلید واقعی اعتبارسنجی نشده است. catalog مستندات account-unverified است.

دموی دو گفت‌وگو: حافظه را روشن کنید؛ در اولی electronics/SELF و ترجیح «قابل‌حمل بودن: بله» را ذخیره و نیاز را
تأیید کنید؛ «پیشنهاد ترجیح برای شناخت من» و «تأیید ترجیح» را بزنید. در گفت‌وگوی تازهٔ هم‌دسته، «استفاده در این خرید»
ترجیح را صریحاً وارد brief تأییدنشده می‌کند. آن را برای این خرید به «خیر» تغییر دهید؛ ترجیح ذخیره‌شدهٔ «بله» مستقل
باقی می‌ماند و قابل حذف است. brief تأییدشده یا مقایسه خودکار بازنویسی نمی‌شود. هدیه/خانه/خودم جدا هستند؛ گفت‌وگوی
بدون حافظه از ترجیحات پایدار نمی‌خواند/نمی‌نویسد. استخراج فقط ساختاریافته است، نه یادگیری آزاد زبان یا ویژگی حساس.

## امنیت، adapter و lifecycle

- migrations افزایشی 0011–0014: settings/memory، credential envelope، revision کلید و aggregate هزینهٔ نشست.
- dependency مستقیم `cryptography==50.0.2`؛ lock شامل `cffi==2.1.1` و `pycparser==3.12`؛ مجوز cryptography:
  Apache-2.0 OR BSD-3-Clause. Fernet/MultiFernet استاندارد با PyNaCl/KMS مقایسه شد؛ SDK موجود OpenAI 3.49.0 و
  httpx2 2.16.0 reuse شدند. رمزنگاری سفارشی یا framework تازه نداریم؛ شواهد در `docs/tooling.md` است.
- master بیرون Git/DB/image است؛ offline بدون master شروع می‌شود و write بدون آن 503 است. replace/delete عملیات
  queued/running وابسته را باطل می‌کند؛ expiry/revision پیش از final publication بازبینی می‌شود. درخواست قبلاً
  ارسال‌شده قابل پس‌گرفتن نیست؛ secret/provider error پیام امن دارد.
- Responses adapter پشت generator موجود با schema محدود clarification، stream، timeout، حداکثر دو attempt،
  cancellation، usage/request ID و `store=false` stub-tested است؛ rank/price/fact قطعی و evidence-bound می‌ماند.
  `store=false` تضمین zero retention نیست؛ AvalAI fallback نداریم. worker واقعی هم با transport ساختگی آزموده شد.
- LiveBudgetLedger موجود reservation/settlement را مالک است؛ aggregateهای GuestContext با purge metadata یا
  تعویض کلید reset نمی‌شوند. missing usage محافظه‌کارانه حساب می‌شود. capهای operation/session/daily پیش‌فرض صفر؛
  خرید با تومان و AI با micro-USD جدا هستند. برآورد ضمانت invoice نیست.
- مدل مستند `gpt-6-luna`: input استاندارد $0.10/M، output $0.50/M؛ cache-write $0.25/M مبنای محافظه‌کارانهٔ input.
  account availability و کیفیت زنده تأیید نشده‌اند. ایران مستقل از key/checkbox blocked است. منابع رسمی در
  `specs/002-personalized-shopping-copilot/openai-readiness.md` ثبت شده‌اند.
- **سیاست موقت توسعه، نیازمند review پیش از انتشار:** candidate هفت روز، confirmed نود روز از اولین تأیید،
  credential سی روز از save/replace؛ configurable، non-sliding و محدود به owner/source expiry. disable با delete
  متفاوت است. حذف source حافظهٔ مشتق‌شده را cascade می‌کند؛ ترجیح اعمال‌شده در brief مقصد مستقل است. cross-browser
  recovery، حذف فوری backup یا بازیابی کلید با master گم‌شده وعده داده نمی‌شود. rotation در operations توضیح دارد.

## بازیابی محیط و داده

پس از آزادشدن 7 GiB، Docker پاسخ داد. PostgreSQL موجود با همان volume
`beforebuy_beforebuy_pgdata_v18:/var/lib/postgresql` شروع شد؛ crash recovery/checkpoint عادی و readiness موفق شدند.
خطای write تازه در بازه‌های بررسی‌شدهٔ DB log دیده نشد؛ repair/reset یا حذف volume انجام نشد.
پیش از migration با API متوقف، backup زیر ساخته شد؛ `pg_restore --list` موفق بود (۲۱۷ خط)، نه restore کامل:

```text
/Users/mehdi/Backups/beforebuy/phase-11-20261115/pre-memory-credentials.dump
mode0600; parent0700; 200133 bytes
SHA-256: 3833d10d45612a82bc5a328498bfbd9af54070e31bdbb997cc8ee7bc2a29f7c2
```

backup و source volume حفظ می‌شوند؛ rollback باید به volume تازه restore کند، نه overwrite دادهٔ موجود.
تمام migrations توسعه اعمال و consistency تأیید شد. master محلی mode0600 در
`/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key` است؛ این فایل API credential نیست.
overlay اختیاری `compose.copilot-secrets.yaml` آن را mount می‌کند؛ خواندن توسط API non-root UID100 این محیط تأیید شد.
مالکیت Linux، ساخت فایل، rotation و بازیابی در `docs/backend-operations.md` توضیح داده شده‌اند.

## verification واقعی

- canonical: `PGCONNECT_TIMEOUT=5 ./scripts/test-backend.sh --keepdb --verbosity 0`:
  **۲۸۳ اجرا/موفق، صفر skipped/failure/error**؛ system check بدون issue.
- دیتابیس آزمون تازه و مجزا: **۲۲/۲۲** تست memory/credential/adapter/config با migrations کامل موفق؛ runner فقط
  همان DB synthetic را حذف کرد. دیتابیس توسعه و backup حفظ شدند.
- RED→GREEN: فراموش‌شدن هزینه پس از purge، snapshot کلید، expiry publication، JSON غیر-object و برچسب worker.
  queued replacement/deletion، no-log key save و SDK timeout نیز آزموده شدند. HTTP 200/401 تست SDK از MockTransport
  است، نه provider. مجموعهٔ متمرکز آخر کلید/adapter ۱۵/۱۵ و worker/concurrency برابر ۱۳/۱۳ موفق بود.
- پس از اصلاح جای‌گذاری skip-link، frontend مجدداً اجرا شد: **۲۱/۲۱ در ۷ فایل** و lint/typecheck/build موفق.
  Docker API/web build موفق، سه سرویس healthy و runtime دوباره mock/OFFLINE تأیید شد.
- Playwright پشت NGINX: journey تنظیمات و دو گفت‌وگو در **390 و 1440 موفق**؛ keyboard، 200% zoom، نبود overflow
  و axe serious/critical صفر. trace/video و screenshot خودکار credential خاموش؛ تصاویر بعد از حذف کلید گرفته شدند.
  اجرای نهایی مشترک با Choice Desk و `--workers=1`: **۴/۴ موفق در 1.7m**؛ تنظیمات 16.1s/17.0s.
- اجراهای اولیهٔ browser شکست داشتند: selector select و انتظار state جدید اصلاح شدند؛ دسکتاپ هم‌زمان با
  build/regression به 75s رسید. rerun همان تست بدون افزایش timeout در 21s موفق شد؛ شکست‌ها موفق شمرده نشدند.
- regression مرتبط Choice Desk ابتدا در هر دو عرض یک پیکسل overflow پیدا کرد: skip-link با margin منفی بیرون
  صفحه قرار داشت. با جای‌گذاری صریح و بدون پنهان‌کردن overflow یا ضعیف‌کردن assertion اصلاح شد؛ rerun در 1440 و
  390 موفق بود (38.0s و 20.3s)، شامل source dialog، keyboard و axe.
- `git diff --check` و `makemigrations --check --dry-run` موفق؛ screenshotهای
  `artifacts/screenshots/copilot-phase11-{settings,memory}-{1440,390}.png` بازبینی شدند.

## اجرای مجدد و gateها

```sh
./scripts/test-backend.sh --keepdb --verbosity 1
export COPILOT_MASTER_KEYRING_PATH=/Users/mehdi/.local/share/beforebuy/secrets/copilot-phase11.key
docker compose -f compose.yaml -f compose.copilot-secrets.yaml up -d --no-build api web
```

Browser runner موجود: `beforebuy-e2e:phase81` با `--network host`،
`PLAYWRIGHT_BASE_URL=http://127.0.0.1:58080`، `PLAYWRIGHT_USE_BUNDLED=1`، `NODE_PATH=/app/frontend/node_modules`؛
`tests/e2e` و `frontend/playwright.config.ts` را read-only در مسیرهای متناظر `/app` mount کنید؛ screenshot directory
در `/app/artifacts/screenshots` و `.runtime/phase11-browser-results` در `/app/frontend/test-results` mount شود؛
فرمان: `npx playwright test --config=playwright.config.ts copilot-settings-memory.spec.ts --reporter=list`.

Gateهای باز: eligibility رسمی OpenAI، validation کلید/مدل حساب، مجوز مستقل هزینه و live evaluation، review سیاست
retention/key operations، source coverage و target-host/public-release rehearsal. feature001 T039 همچنان pending است.

## Git

این handoff همراه تغییرات مرتبط Phase11 برای origin موجود `medyrad/beforebuy` آماده شده؛ hash و نتیجهٔ push در گزارش
نهایی اعلام می‌شود. حذف نامرتبط `test.txt` و چهار screenshot قدیمی Phase8/9.2 خارج commit می‌مانند.
secret، backup، runtime DB/log/trace و محیط‌های محلی وارد Git نمی‌شوند.
