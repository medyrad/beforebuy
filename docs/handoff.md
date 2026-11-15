# تحویل Phase 9 — Milestone B: پژوهش محدود و evidence

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline بازبینی‌شده:** `09e8dff14c42e87c3cdf21a317bcc28f0a455b9e`  
**branch:** `002-personalized-shopping-copilot`  
**وضعیت:** زیرساخت evidence و fixture research verify شد؛ live allowlist خالی و پوشش source کامل نیست  
**taskهای کامل:** `T014–T017`, `T020–T023`  
**taskهای partial و باز:** `T013`, `T018`, `T019`  
**taskهای خارج scope:** Milestoneهای C–E باز؛ هر دو feature-specific `T039` بدون تغییر و pending

## دامنه و نتیجه

Phase 9 entityهای پژوهش، migration غیرمخرب، safe-fetch، extraction/identity قطعی، cache/cleanup، coordinator و API
حداقلی start/status/cancel را روی lifecycle موجود `StreamOperation`/`StreamEvent` افزود. default برنامه `OFFLINE` است؛
`FIXTURE` فقط با label صریح فعال می‌شود و `LIVE` با نبود source مجاز `NO_SUPPORTED_SOURCES` می‌دهد و outbound صفر دارد.
هیچ ranking/Choice Desk Milestone C، memory، credential، provider/model call، پرداخت، public deployment یا route cutover
انجام نشد. حذف نامرتبط `test.txt` حفظ و از commit کنار گذاشته می‌شود. handoff قبلی در
`docs/archive/phase-8.1-handoff.md` آرشیو شد.

## Spec Kit و task truth

- prerequisite رسمی feature `002-personalized-shopping-copilot` و checklist `requirements.md` برابر 16/16 بود؛
  `.specify/extensions.yml` وجود نداشت.
- `$speckit-analyze` پیش از implementation سه gap High در حدود دقیق B، retention و قرارداد API و یک gap Medium در
  گستردگی T023 یافت. اصلاحات مجاز در `FR-044–FR-049`، plan، data model، OpenAPI و تفکیک statusها ثبت شد. rerun پس از
  اصلاح Critical/High یا placeholder نیافت؛ incomplete source coverage به‌عنوان blocker واقعی task حذف یا ضعیف نشد.
- `$speckit-implement` فقط `T013–T023` را اجرا کرد. `T014–T017` و `T020–T023` complete شدند. `T013` به‌علت نبود
  permission/retention/display روشن برای enablement، و `T018/T019` به‌علت نبود sports source/fixture مجاز باز و partial
  ماندند. Milestoneهای C–E و feature 001/002 `T039` unchecked هستند.

## feasibility منبع و probe زنده

هفت GET عمومی کم‌حجم، read-only و بدون retry اجرا شد؛ proxy محیطی استفاده نشد، redirect حداکثر ۲، decoded cap برابر
۲ MiB و timeout برابر ۲۰ ثانیه بود. فایل خام probe فقط در `/tmp` بود و وارد Git نشد. provider/model call و هزینه صفر.

| Source | درخواست Phase 9 | مشاهده و extraction | readiness / enablement |
|---|---:|---|---|
| Philips `www.philips.com` | ۲ | robots: 200/254 B؛ صفحه EP5934: 200 HTML/33,782 B/0 redirect/0.330s؛ JSON-LD name, brand, SKU, MPN=`EP5934/10R1` | `CAPTURED_REAL_FIXTURE` + `LIVE_PROBE`؛ disabled تا روشن‌شدن permission/retention/display |
| Technolife `www.technolife.com` | ۳ | robots: 200/589 B؛ terms: 200/134,718 B؛ A56: 200 HTML/147,320 B/0 redirect/0.485s؛ identity `99474` و متن دقیق `ناموجود`؛ price/shipping/total absent | `CAPTURED_REAL_FIXTURE` + `LIVE_PROBE`؛ disabled تا clarification کتبی |
| Torob `torob.com` | ۲ | robots: 200/110 B؛ terms: 200/11,234 B؛ product request و offer extraction انجام نشد | `LIVE_PROBE` policy-only؛ disabled |
| Apple | ۰ | terms automated page scraping/robot را منع می‌کند | disabled |
| Adidas / Decathlon | ۰ | terms برای automated access به permission/consent کتبی نیاز دارد | disabled؛ sports blocker |
| Nike / Digikala | ۰ | Phase 7 permission/timeout unresolved؛ retry تکراری انجام نشد | disabled/unassessed؛ timeout عدم دسترسی دائمی نیست |

بنابراین enabled live source دقیقاً صفر است. Philips manufacturer claim است و اندازه‌گیری مستقل performance نیست.
Technolife fixture فقط availability تاریخی out-of-stock دارد و price/current stock یا cheapest-in-Iran را پشتیبانی
نمی‌کند. fixtureهای حداقلی checksummed هستند: Philips
`4962e609585514bf48ad6026c7309feeb4e2c680003f86bcf364eae0f700d424` و Technolife
`87f2d00a9abf19b4ddb84da8a9ce41ab03ed348398ebc3e0e15840d1c529921c`.

## safe fetch، limits و dependency

- transport از Python stdlib 3.12 (`http.client`, `ssl`, `socket`, `ipaddress`) استفاده می‌کند؛ dependency و lockfile
  تازه‌ای اضافه نشد. skill محلی validated در `.agents/skills/bounded-product-research/` مرز DNS/pinning/source truth را
  ثبت می‌کند.
- scheme فقط HTTP(S)، port/hostname/path/redirect exact policy، embedded credential ممنوع، و همهٔ DNS answerها باید
  public/global باشند. connection واقعی به IP تأییدشده pin می‌شود، ولی TLS SNI/certificate verification و Host اصلی
  حفظ می‌شوند. redirect دوباره validate می‌شود؛ proxy env، cookie و credential وارد fetch نمی‌شوند.
- limits مصوب و persisted: ۳ domain/job، ۵ page/domain، ۲ redirect/request، ۲۰ HTTP request/job، ۲ MiB decoded/page،
  ۲۰s/request، ۶۰s/job، pace حداقل ۱s/domain، outbound concurrency دو/process و یک active job/guest. retry خودکار وجود
  ندارد؛ در نتیجه Retry-After دنبال نمی‌شود و loop نامحدود ممکن نیست. semaphore per-process deployment-global نیست.
- research executor و admission از conversation executor جداست تا fetch کار status/cancel را exhaust نکند. network
  در transaction اجرا نمی‌شود. lease ۳۰s قبل از هر work unit renew و publication بعد از I/O دوباره owner، expiry،
  brief revision، cancel و conversation expiry را زیر lock order `Conversation → StreamOperation → ResearchJob`
  می‌سنجد. restart network work را خودکار تکرار نمی‌کند.

## داده، provenance، cache و lifecycle

Migration `0006_copilot_milestone_b` مدل‌های `SourcePolicy`, `ResearchJob`, `SourceSnapshot`, `EvidenceClaim`, `Product`,
`Variant`, `Offer` و `operation_kind` را بدون دست‌زدن به rowهای feature 001 افزود. هر snapshot retrieval time، source
role، MIME/status/bytes، fingerprint، extractor version و failure را دارد؛ claim به field/value/location و status
متصل است. Offer item/shipping/total/seller/condition/availability/observed time را جدا نگه می‌دارد؛ shipping نامعلوم
یعنی total نامعلوم.

raw cache حداکثر ۲۴ ساعت و non-sliding است. cache hit timestamp و expiry اصلی را حفظ می‌کند و فقط داخل همان conversation
reuse می‌شود. conversation delete/expiry snapshot/claim/offer را cascade می‌کند؛ cleanup raw منقضی را null و فقط
Product/Variant کاملاً orphan را حذف می‌کند، بنابراین identity هنوز referenced حذف نمی‌شود. backup erasure فوری وعده
داده نمی‌شود و تابع lifecycle backup است.

## API و smoke واقعی Compose

OpenAPI برای start/status/cancel، typed job/snapshot/claim/coverage/error و `operation_kind` تکمیل شد. start به brief
تأییدشده، expected revision، CSRF و idempotency key نیاز دارد. GET/status/replay work را آغاز نمی‌کند. active limit
guest-wide است؛ foreign owner 404 می‌گیرد؛ cancel terminal است؛ progress فقط completed unit را می‌شمارد. outcomeهای
`SUCCESS`, `PARTIAL_SUCCESS`, `NO_SUPPORTED_SOURCES`, blocked/extraction/timeout/cancel/interrupted/failed جدا هستند.

Compose با `BEFOREBUY_RESEARCH_MODE=FIXTURE docker compose up --build -d` بازسازی شد؛ migration 0006 اعمال و هر سه
service healthy شدند. smoke از NGINX روی `127.0.0.1:58080` مسیر session → conversation → brief edit/confirm → research
را اجرا کرد: `SUCCESS`, `completed=2`, `total=2`، دو snapshot، چهار claim دارای variant identity،
`fixture_labeled=true` و `canonical_url=null` برای هر دو.
سپس API با env unset force-recreate شد؛ env واقعی `OFFLINE`، service healthy و start از NGINX برابر
`HTTP 409 RESEARCH_OFFLINE` بود. volume reset یا public deploy انجام نشد.

## verification

- TDD RED اولیه: شش import error برای مدل/moduleهای مفقود؛ سپس failures هدفمند برای PostgreSQL lock، executor double،
  deadline، Technolife fallback و raw-cache cleanup ثبت و علت‌ها اصلاح شدند.
- focused نهایی research/migration/cleanup: ۳۹ test، passed ۳۹، failed/error/skipped صفر در 5.675s؛ findingهای
  orphan identity، variant API attribution و pacing deadline در همین مجموعه پوشش داده شدند.
- canonical backend نهایی از root: `./scripts/test-backend.sh --verbosity 1` → ۲۱۴ discovered/run، ۲۱۴ passed،
  skipped ۰، failed/error صفر در 41.196s.
- `manage.py check` بدون issue؛ `makemigrations --check --dry-run` → `No changes detected`؛ compileall، skill validator،
  JSON manifest، OpenAPI YAML و `git diff --check` موفق. `check --deploy` با settings تولید در container توسعه به‌درستی
  روی `DJANGO_DEBUG=1` fail-closed شد و به‌عنوان pass شمرده نشد.
- browser smoke از image رسمی Playwright 1.65.1 digest
  `sha256:1507cbfc550a63a6b7396791ca4f00df17beb56342d2447b3f106c306f525579` و NGINX واقعی: ۳/۳ passed در 26.3s؛
  desktop/accessibility، mobile/keyboard و legacy route. اجرای host Node قبل از discovery به علت dyld/Hermes نامعتبر بود؛
  اجرای container معیار نهایی است.
- live public source probe: ۷ request، سه domain، zero retry. runtime live research call: صفر؛ provider/model call: صفر؛
  paid activity: صفر.

## gateها و ادامهٔ مجاز بعدی

1. Philips/Technolife/Torob باید permission، retention، display/attribution و rate contract را روشن کنند؛ بدون آن
   `T013` و live allowlist باز است.
2. sports source مجاز و direct extraction لازم است تا `T018/T019` کامل شوند. Iranian current offer، shipping و total
   نیز هنوز evidence ندارد.
3. process-local semaphore global cap نیست؛ چند worker حداکثر مستقل دارند. durable queue/Redis بدون evidence نیاز اضافه
   نمی‌شود.
4. Milestone C ranking/Choice Desk، D memory/credential/OpenAI و E pilot/deployment gateها مجوز جدا می‌خواهند.
5. feature 001 `T039` تا live provider evidence + human review و feature 002 `T039` تا direct OpenAI eligibility/authorization
   هر دو pending هستند. هیچ market comparison یا best-price recommendation پیاده نشده است.

## Git

فقط code/test/migration/skill/spec/contracts/docs/Compose مرتبط Phase 9 stage می‌شود. `.env`، credential، database، dump،
log، cache، browser artifact و حذف نامرتبط `test.txt` وارد commit نمی‌شوند. branch جاری به origin موجود push می‌شود؛
merge، force-push و remote جدید انجام نمی‌شود.

**Milestone B partially complete — source/check blockers listed.**
