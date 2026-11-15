# آرشیو تحویل Phase 8 — Milestone A conversational foundation

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline بازبینی‌شده:** `0292c71f53b676996a6a8f776ec5d6865c47675f`  
**branch:** `002-personalized-shopping-copilot`  
**وضعیت:** Milestone A پیاده و verify شده؛ فقط fixture streaming، بدون AI زنده یا پژوهش بازار  
**taskهای کامل feature 002:** `T001–T012`, `T049`  
**taskهای باز:** `T013–T048`, `T050`؛ از جمله `T043` کامل نشده است  
**feature 001:** `T039` قدیمی همچنان pending و مستقل است

## نتیجه

مسیر غیراصلی `/copilot` اکنون یک shell فارسی/RTL واقعی برای conversation، brief قابل‌ویرایش، upload محافظت‌شده و
پاسخ incremental از generator قطعی fixture دارد. مسیر `/` و همهٔ رفتار feature 001 حفظ شده‌اند. Choice Desk در A
عمداً readiness خالی و صادقانه است: product، قیمت بازار، review، ranking، offer یا citation ساختگی نمایش داده نمی‌شود.
هیچ provider call، research-network call، crawl، persistent memory یا credential storage اجرا/اضافه نشده است.

## Spec Kit و تحلیل

- prerequisite رسمی با `--require-spec --require-tasks --include-tasks` feature 002 و artifacts را پیدا کرد؛ checklist
  requirements برابر `16/16` checked بود.
- `speckit-analyze` پیش از implementation دو finding سطح High پیدا کرد: retention هنوز در یک artifact proposal بود و
  ownership cleanup کامل نبود. هر دو در spec/plan/data model/decisions/tasks اصلاح شدند. تحلیل همگرایی نهایی روی 40 FR،
  8 SC و 50 task، تعارض Critical/High، placeholder و task بدون هدف در scope جاری پیدا نکرد؛ coverage task برای
  requirementهای feature کامل باقی ماند.
- `speckit-implement` فقط authorization صریح `T001–T012` و `T049` را اجرا کرد. taskهای بعدی و T043 باز ماندند.
- Phase 7 handoff بدون حذف محتوا به `docs/archive/phase-7-handoff.md` منتقل شد.

## اصلاح design، contract و lifecycle

- Concept 2 به off-white/cool-gray با accent محدود indigo، Vazirmatn موجود، navigation در لبهٔ راست، conversation در
  راست و Choice Desk بزرگ‌تر در چپ با نسبت تقریبی 5/7 بازگردانده شد. mobile switch state draft را حفظ می‌کند.
- shortlist آینده دقیق شد: محصول انتخابی کاربر، اگر موجود باشد، به‌علاوهٔ حداکثر سه alternative؛ merchant offerها
  فهرست جدا هستند. UI کامل comparison همچنان Milestone C است.
- OpenAPI 3.1 در `/api/v1` برای session موجود، conversation CRUD/list، brief CAS/confirm، message idempotency، operation
  status/SSE/cancel و upload access/delete schema و example اجرایی دارد. routeهای milestone بعدی فقط planned هستند.
- retention مصوب A: conversation/message/current brief تا 90 روز پس از آخرین accepted user message یا brief
  edit/confirmation؛ upload و event حداکثر 24 ساعت. read/list/SSE/replay/background anchor را تمدید نمی‌کند. replay gap
  با `409 REPLAY_GAP` و REST reconcile می‌شود، نه regeneration. حذف conversation publication دیرهنگام را باطل می‌کند.
- cleanup همان command موجود است و اکنون expired conversation/upload bytes/events را نیز پاک می‌کند، اما owner دارای
  conversation فعال را حذف نمی‌کند. backup فوری پاک‌شده ادعا نمی‌شود و feature 001 expiry تغییر نکرده است.

## مدل اجرا و محدودیت restart

`POST message` در transaction کوتاه Message و StreamOperation را ثبت می‌کند و فقط با `transaction.on_commit` به
executor process-local می‌سپارد. هر process دو worker و queue ظرفیت چهار دارد؛ برای هر guest حداکثر دو operation
`PENDING|RUNNING` پذیرفته می‌شود. worker با conditional update در PostgreSQL claim و lease می‌گیرد. event sequence،
cancel flag، revision/generation guard و terminal state در PostgreSQL shared truth هستند؛ هیچ lock در generation یا
انتظار stream نگه‌داری نمی‌شود.

این executor durable نیست. process crash/restart یا lease stale operation را `INTERRUPTED` می‌کند، خودکار restart
نمی‌کند و publish دوباره نمی‌پذیرد. retry کنترل‌شده operation تازه و idempotency key تازه می‌سازد. browser disconnect
execution را لغو نمی‌کند؛ cancel صریح endpoint مستقل دارد. Gunicorn با 2 worker از نوع `gthread` و 4 request thread
در هر worker اجرا می‌شود تا status/cancel پشت subscriberهای SSE نمانند.

## backend و migration

- migration غیرمخرب `0005_copilot_milestone_a.py` مدل‌های Conversation، ShoppingBrief، Message، StreamOperation،
  StreamEvent و UploadedImage را اضافه می‌کند. upgrade test از schema `0004` یک Analysis feature 001 را سالم نگه داشت.
- owner/session/CSRF موجود reuse شد؛ foreign و expired IDها disclosure نمی‌دهند. brief revision CAS، digitهای فارسی/
  عربی/لاتین، تومان، صفر در برابر unknown، self/gift/household، contradiction و unknown صریح هستند.
- generator فقط fixture قطعی و بی‌ادعای بازار است. unsupported free text پاسخ روشن development-mode می‌گیرد؛ NLP
  عمومی یا keyword assistant پنهان وجود ندارد.
- SSE eventهای versioned و monotonic، replay/deduplication، provisional/final، heartbeat comment، cancel/fail/
  interrupted و stale publication guard دارد. GET/SSE execution را شروع یا تکرار نمی‌کنند.
- upload: حداکثر 3 فایل فعال در conversation، raw ≤5 MiB، هر محور ≤4096 و ≤12MP؛ فقط decoded JPEG/PNG/WebP، تک‌فریم،
  decode/re-encode و حذف metadata. SVG/HTML/invalid/multiframe/decompression-bomb رد می‌شود. bytes sanitized در PostgreSQL
  named volume هستند و فقط endpoint owner-scoped ارائه می‌شوند؛ filename اصلی نگه‌داری نمی‌شود.

## frontend و Docker

- `CopilotApp` و client/types/icons در `frontend/src/features/copilot/conversation/` اضافه شدند. `/copilot` مستقل است و
  `/` همان LegacyApp باقی مانده است.
- UI شامل history/create/open، brief ribbon/editor، composer، image status، incremental reply و send/stop/retry است؛
  development/fixture و «بدون AI زنده» همیشه قابل مشاهده‌اند. text به‌صورت React text render می‌شود و HTML اجرا نمی‌شود.
- `compose.yaml` stack offline کامل db/api/web را پشت NGINX روی loopback ارائه می‌کند. web/API/database به‌ترتیب
  `127.0.0.1:58080`, `127.0.0.1:58000`, `127.0.0.1:55439` هستند. volume موجود reset یا حذف نشد.
- NGINX فقط prerequisite SSE مربوط T009 را جلو آورد: buffering/cache/gzip برای event stream خاموش و timeout محدود است.
  full graceful-shutdown/production rehearsal در T043 همچنان باز است.

startup دقیق، پس از بازبینی `.env`:

```bash
docker compose up -d db
docker compose run --rm api python backend/manage.py migrate --noinput
docker compose up --build -d --wait
```

Browser: `http://127.0.0.1:58080/copilot`؛ legacy: `http://127.0.0.1:58080/`.

## dependency و tooling

- تنها dependency runtime تازه `Pillow==13.0.0` با license MIT-CMU برای decode/sanitize image است؛ در `uv.lock` قفل شد.
- queue، Redis، Celery، WebSocket framework، provider framework، UI framework یا object storage افزوده نشد.
- Playwright `1.65.1` با image رسمی pinned به digest
  `sha256:1507cbfc550a63a6b7396791ca4f00df17beb56342d2447b3f106c306f525579` فقط برای test استفاده شد.
- skill `frontend-design` در catalog native همین session کشف و invoke شد؛ overlay پروژه Persian/RTL/accessibility را مقدم کرد.

## verification با خروجی بازبینی‌شده

- backend canonical PostgreSQL: `Found 164 test(s)`، `Ran 164 tests in 21.649s`، `OK`؛ passed `164`، skipped `0`،
  failed `0`، errors `0`. شامل regressionهای feature 001، model/constraint، ownership/CSRF، cleanup، money/CAS، upload،
  SSE/replay/idempotency، raceهای PostgreSQL و migration upgrade است.
- migration consistency: `makemigrations --check --dry-run` → `No changes detected`. full suite database خالی را از
  `0001` تا `0005` migrate کرد؛ development DB موجود فقط `0005` را با `OK` گرفت و data/volume reset نشد.
- frontend: 4 test file و 13 test؛ passed `13`، skipped/failed/errors `0`. TypeScript typecheck، ESLint و production
  Vite build موفق؛ bundle اصلی JS برابر 264.46 kB و gzip برابر 81.85 kB بود.
- Playwright از image رسمی و مسیر واقعی NGINX/API: 3 test در 14.6s، passed `3`، skipped/failed `0؛` viewportهای
  `1440×1000` و `390×844`، keyboard/focus، reduced motion، state-preserving mobile navigation، mixed bidi/long Persian،
  direct refresh، legacy `/` و axe serious/critical برابر صفر.
- proxy streaming smoke واقعی: first event حدود `440ms` پیش از terminal مشاهده شد؛ دو subscriber همان operation را
  دیدند، subscriber count `2`، final message ذخیره‌شده `1`، status هنگام stream `RUNNING` و terminal `COMPLETED` بود.
  این fixture evidence است، نه AI زنده.
- Compose پس از rebuild هر سه service را healthy نشان داد؛ API/DB ports فقط loopback منتشر شدند. هیچ provider یا
  research-network call اجرا نشد؛ هزینه provider صفر است.
- `git diff --check` بدون خطا و OpenAPI schema/examples/operation IDs در backend suite parse و validate شدند.

## بررسی بصری و screenshot

- `docs/screenshots/copilot-phase8-desktop-1440.png`: navigation تیره در راست، conversation panel راست، Choice Desk
  بزرگ‌تر چپ، brief بالای Desk، متن fixture و `<script>` به‌صورت inert text، بدون card/price/ranking ساختگی.
- `docs/screenshots/copilot-phase8-mobile-390.png`: Desk تک‌ستونه، متن خوانا بدون overflow افقی، switch پایین با focus
  indigo واضح و state draft حفظ‌شده. رنگ saffron وارد design جدید نشده است.

## محدودیت‌ها و gateهای باز

1. فقط generator fixture است؛ AI زنده، OpenAI/AvalAI، crawl، source extraction، market offer و ranking وجود ندارد.
2. Milestoneهای B–E (`T013–T048`, `T050`) بازند؛ T043 فقط prerequisite کوچک گرفته و complete نیست.
3. memory، user key، encryption و export هنوز پیاده نشده‌اند. retention آن entityها همچنان نیازمند تصمیم milestone مربوط است.
4. public deployment، target-host verification، source terms/permission، direct OpenAI region eligibility و spending
   authorization gateهای جدا هستند.
5. feature 001 `T039` با fixture feature 002 کامل نمی‌شود و همچنان live evidence + human review می‌خواهد.

## working tree و محرمانگی

حذف نامرتبط `test.txt` از ابتدای کار حفظ شده و در commit Phase 8 stage نمی‌شود. هیچ `.env`، credential، secret، dump،
database file، cache، `node_modules` یا runtime report وارد Git نمی‌شود.

**Milestone A implemented and verified — fixture streaming only**
