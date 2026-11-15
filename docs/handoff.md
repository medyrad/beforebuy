# تحویل Phase 8.1 — اصلاحات bounded streaming در Milestone A

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline بازبینی‌شده:** `9658dc93d5df058589b5dd143dab37ebcd160938`  
**branch:** `002-personalized-shopping-copilot`  
**وضعیت:** اصلاحات streaming در Milestone A verify شده؛ فقط fixture، بدون AI زنده یا پژوهش بازار  
**taskهای اصلاحی کامل:** `T051`, `T052`, `T053`, `T054`  
**taskهای بعدی:** `T013–T048`, `T050` باز؛ Milestone B شروع نشده و feature 001 `T039` همچنان pending است

## دامنه و نتیجه

Phase 8.1 فقط مرز final publication، lifecycle/replay در SSE و admission/failure executor را اصلاح کرد. هیچ crawl،
source expansion، ranking، Choice Desk جدید، memory، credential، provider call، AI زنده، deployment عمومی یا migration
داده‌ای اجرا نشد. حذف نامرتبط `test.txt` حفظ و از stage این phase کنار گذاشته می‌شود. handoff قبلی بدون حذف محتوا در
`docs/archive/phase-8-handoff.md` آرشیو شد.

## یافته‌های بازبینی

همهٔ findingهای consequential تأیید شدند:

- FINAL message پیش از دو final event commit می‌شد و می‌توانست روی operation ناموفق/لغوشده باقی بماند.
- publication lease owner/expiry و expiry conversation را در هر مرز دوباره اعتبارسنجی نمی‌کرد و lease تمدید نمی‌شد.
- reconciler از snapshot قدیمی تصمیم می‌گرفت و امکان interrupt کردن claim/renew تازه وجود داشت.
- SSE عمر نامحدود، admission صریح و reconciliation در stream باز نداشت.
- replay فقط retained row اول را می‌دید؛ all-purged و future sequence می‌توانستند 200 خالی و UI منتظر بسازند.
- executor submit failure slot را پس نمی‌داد و operation را `PENDING` رها می‌کرد؛ stale pending نیز quota را نگه می‌داشت.
- client روی `EventSource.onerror` اتصال را می‌بست و REST authoritative reconciliation/reconnect نداشت.

هیچ findingی به‌عنوان false positive رد نشد. نیاز به migration جدید نیز رد شد: `next_sequence` موجود همان authoritative
highest-sequence boundary لازم را فراهم می‌کند.

## Spec Kit

- سه requirement محدود `FR-041–FR-043` و چهار task اصلاحی `T051–T054` اضافه شدند؛ taskهای تاریخی renumber نشدند.
- `$speckit-analyze` پس از prerequisite رسمی و checklist `16/16`، در scope اصلاحی تعارض Critical/High، placeholder یا
  requirement بدون task پیدا نکرد.
- `$speckit-implement` فقط `T051–T054` را اجرا کرد. Milestoneهای بعدی و `T043` کامل علامت نخورده‌اند.

## finalization و lock order

lock order همهٔ مسیرهای اصلاح‌شده `Conversation → StreamOperation` است. lookup اولیهٔ `conversation_id` lock نیست؛ سپس
conversation و operation در transaction کوتاه lock می‌شوند. message acceptance همچنان ابتدا GuestContext و بعد
Conversation را می‌گیرد و هیچ مسیر معکوس Conversation→GuestContext وجود ندارد. generation یا انتظار SSE lock نگه نمی‌دارد.

`finalize_operation` در یک transaction موارد زیر را دوباره می‌سنجد: وجود/expiry conversation، `RUNNING` بودن، revision،
cancel، lease owner و تازه‌بودن lease. سپس FINAL Message، `assistant.message.final`، `operation.completed`، pointer نهایی،
`next_sequence` و state `COMPLETED` را با هم commit می‌کند. failure تزریقی در ساخت event دوم همه را rollback می‌کند.
mutationی که lock/commit را اول بگیرد برنده است: cancel/edit/delete زودتر مانع final می‌شود؛ completion زودتر باعث 409
برای cancel بعدی است. worker با owner عوض‌شده یا lease منقضی هیچ event، حتی failure event، منتشر نمی‌کند.

brief edit با revision mismatch به `INTERRUPTED/STALE_BRIEF` می‌رسد؛ explicit cancel به‌صورت فوری و اتمیک event
`operation.cancelled` و state `CANCELLED` می‌سازد. delete با lock conversation cascade می‌کند. event پس از expiry
conversation ساخته نمی‌شود.

## stale operation، SSE و replay

- claim lease سی‌ثانیه‌ای می‌سازد؛ هر publication معتبر lease را تمدید می‌کند. reconciler فقط پس از re-read زیر lock
  دربارهٔ pending قدیمی، lease منقضی، cancel، revision یا expiry تصمیم می‌گیرد.
- هر SSE حداکثر 45 ثانیه، heartbeat حداکثر 15 ثانیه و poll برابر 80ms دارد. دو subscriber در هر application process
  admitted می‌شوند و slot در terminal، timeout، disconnect یا response close دقیقاً یک بار آزاد می‌شود.
- Gunicorn دو worker × چهار gthread دارد، ولی این به‌تنهایی policy نیست؛ semaphore دو subscriber در هر process دو
  request thread را برای status/cancel آزاد نگه می‌دارد. subscriber سوم `429 STREAM_CAPACITY_REACHED` می‌گیرد.
- `next_sequence - 1` highest issued است. no-history معتبر است؛ latest terminal فوراً می‌بندد؛ future sequence با
  `409 INVALID_REPLAY_SEQUENCE` و partial/all-purged history با `409 REPLAY_GAP` پاسخ می‌گیرد. هر دو 409 REST URL دارند.
- purge race پس از شروع response، control event غیرپایدار `stream.replay_gap` می‌دهد. client EventSource را می‌بندد و
  operation را از REST poll می‌کند؛ خطای عادی stream ابتدا REST را می‌خواند و برای state فعال native reconnect را باز
  می‌گذارد. هیچ مسیر reconciliation generator را دوباره اجرا نمی‌کند.

## executor admission و failure

reservation پیش از acceptance گرفته می‌شود؛ outer transaction callback submit را فقط پس از commit اجرا می‌کند.
rollback/replay reservation را برمی‌گرداند، submit failure operation را با event صریح `FAILED/SUBMISSION_FAILED`
terminal می‌کند و slot را دقیقاً یک بار آزاد می‌کند، و worker در همهٔ exit pathها slot خود را آزاد می‌کند. queued cancel
فوراً terminal می‌شود؛ worker دیرتر claim نمی‌کند. quota فقط PENDING تازه یا RUNNING با lease تازه را می‌شمارد، بنابراین
stale pending مانع پذیرش کار تازه نمی‌شود؛ خود stale operation هنگام status/SSE authoritative reconcile می‌شود.

## verification اجراشده

- RED متمرکز پیش از implementation: 17 test کشف شد؛ 3 failure و 2 import/error دقیقاً برای all-expired replay، future
  sequence، admission API، submit failure و helperهای lease/finalization ثبت شد.
- regression متمرکز PostgreSQL پس از اصلاح: 30 test، passed 30، failed/error/skipped صفر. barrierهای
  threading در خود final-publication boundary و mutationهای واقعی brief/cancel/delete API استفاده شدند؛ sleep-only نیستند.
- backend canonical نهایی: `Found 179 test(s)`، `Ran 179 tests in 51.034s`، `OK`؛ passed 179، failed/error/skipped صفر.
- migration drift: `makemigrations --check --dry-run` → `No changes detected`. compileall و `git diff --check` موفق.
- frontend: 4 file و 15 test، passed 15؛ typecheck، ESLint و build موفق. bundle اصلی JS `265.01 kB` و gzip `82.00 kB`.
- browser از image رسمی Playwright 1.65.1 و stack بازسازی‌شدهٔ NGINX/API: 3/3 passed در 11.8s؛ desktop/mobile،
  accessibility و legacy route. اجرای اول با hostname روش test (`host.docker.internal`) طبق انتظار Django با
  `DisallowedHost` رد شد؛ بدون تضعیف host validation، اجرای صحیح `--network host` روی `127.0.0.1` کامل موفق شد.
- NGINX cancel smoke واقعی: started event مشاهده شد؛ cancel response و REST هر دو `CANCELLED`، terminal event دقیقاً یک،
  reconnect از latest برابر zero-byte clean close.
- NGINX disconnect/reconnect smoke واقعی: stream اول یک `operation.started` داشت؛ reconnect از همان ID started را تکرار
  نکرد، `operation.completed` را گرفت و REST `COMPLETED` بود. generator دوباره اجرا نشد.
- provider/research call صفر و هزینه صفر؛ development/backup volume حذف یا reset نشد.

## محدودیت‌ها و gateهای باقی‌مانده

1. executor process-local و غیردوام‌دار است؛ restart کار را resume نمی‌کند و فقط `INTERRUPTED` + retry صریح دارد.
2. admission per-process است، نه global. بدون Redis/queue جدید، توزیع subscriber میان processها تضمین دقیق global ندارد.
3. SSE thread را تا 45 ثانیه اشغال می‌کند؛ policy دو subscriber ظرفیت cancel/status را حفظ می‌کند ولی جای durable async
   infrastructure نیست.
4. `T043` برای production graceful shutdown/rehearsal کامل، و تمام Milestoneهای B–E باز هستند.
5. AI زنده، source permission، target-host verification، public release و feature 001 `T039` gateهای مستقل و بازند.

## Git و working tree

فقط code/test/spec/contract/operations/handoff مرتبط Phase 8.1 stage می‌شود. `.env`، secret، database، dump، log، cache،
`node_modules`، Playwright runtime artifacts و حذف نامرتبط `test.txt` وارد commit نمی‌شوند. branch جاری به remote موجود
push می‌شود؛ merge، force-push یا remote جدید مجاز نیست.

**Milestone A streaming corrections verified — fixture-only.**
