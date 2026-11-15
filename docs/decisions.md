# ثبت تصمیم‌ها

## Phase 11.1 — contextual assistant closure

- T071–T077 are authorized for bounded contextual assembly, typed answer validation, meaningful safe streaming,
  SDK model-list seam and synthetic in-app demonstrations. No live provider/source call or Milestone E work is allowed.
- Provider input is ephemeral and bounded. StreamOperation persists only a non-secret context manifest/fingerprint;
  it pins current turn, brief/generation, model settings, ChoiceSet/evidence, uploads and included memory revisions.
- Model output is a typed answer plan, not authoritative prose. Candidate/value/attribution/freshness/variant checks
  precede deterministic Persian factual rendering. Residual free-form semantic entailment is not claimed solved.
- Safe context-aware lead text may stream before plan completion; validated block text follows validation. Neither is
  authoritative until final publication. No artificial typing delay is presented as provider streaming.
- Account model refresh is an explicit future action behind region and validated-credential gates. Model IDs returned
  by `models.list()` are intersected with documentation metadata and never imply capabilities or pricing by themselves.

## Phase 11 — authorized development and provisional lifecycle

- Session spending uses durable guest aggregates in the existing LiveBudgetLedger; purging 90-day invocation
  metadata or replacing a key does not renew the cap. Accounting money remains micro-USD, not purchase toman.
- T032–T041 مجازند؛ هیچ provider/source call، deployment یا evaluation پولی مجاز نیست. تنظیمات و حافظه در
  /copilot قابل دسترسی‌اند؛ legacy route حفظ می‌شود. ذخیرهٔ کلید validation نیست و ایران مستقل از key blocked است.
- **پیشنهاد موقت توسعه، نیازمند review پیش از public/live activation:** candidate از ایجاد ۷ روز، confirmed از
  تأیید ۹۰ روز و credential از save/replace سی روز؛ configurable، non-sliding و محدود به عمر دسترسی owner.
  edit/read تمدید نمی‌کند. حذف/expiry گفت‌وگوی مبدأ همهٔ memory مشتق‌شده را cascade می‌کند.
- disable حافظه فقط reuse/proposal را متوقف می‌کند؛ delete/clear حذف active rows است، نه erase فوری backup.
  temporary conversation از ابتدا immutable است و memory نمی‌خواند/نمی‌نویسد. بازیابی cross-browser وجود ندارد.
- استخراج فقط از criteria ساختاریافتهٔ brief تأییدشده، با action کاربر و وضعیت candidate است؛ NLP یا یادگیری
  گسترده ادعا نمی‌شود. reuse جداگانه، قابل مشاهده و فقط روی brief تأییدنشده است؛ دستور صریح جاری مقدم است.
- encryption: pyca cryptography 50.0.2 (Apache-2.0 OR BSD-3-Clause)، Fernet data key تصادفی per record و
  wrap با MultiFernet master keyring بیرون DB/image/Git. PyNaCl SecretBox گزینهٔ معتبر ولی نیازمند عملیات rotation
  بیشتر است؛ KMS سرویس اضافی نامتناسب با محیط محلی است. گم‌شدن master بدون نسخهٔ امن یعنی عدم بازیابی کلید؛
  rotate فقط wrapped data key را تغییر می‌دهد و expiry/credential revision را تمدید نمی‌کند.

## Phase 9.3 — connectivity and review provenance

- Local-only, no AI token/provider needed. At most 30 outbound attempts; one existing Torob URL first.
- SafeFetcher may attempt at most two distinct fully validated public IPs before sending HTTP, using shared
  request/job deadlines and the existing request/domain budget. No fallback on HTTP/parser/policy failure.
- Source toggles preserve review timestamps/readiness. New rows use null exact timestamps with dated review evidence.
- Fresh host/container TLS succeeded and HTTP 490 prevented extraction. Its remote cause is unresolved; neither
  first-address selection nor missing AI credentials explains this observation. Captured data is not live proof.
- T066 remains open; default OFFLINE/disabled policies restored. No network relocation or later milestone approved.

این سند چهار وضعیت را جدا نگه می‌دارد. جابه‌جایی هر مورد بین بخش‌ها باید با تصمیم صریح و به‌روزرسانی specificationهای متاثر انجام شود.

## تصمیم‌های تاییدشده توسط کاربر

- frontend با React.
- backend با Django.
- deployment به‌صورت Dockerized.
- Spec-Driven Development با GitHub Spec Kit رسمی.
- استفاده از مهارت مرتبط برای هر دسته کار substantive.
- پرهیز از overengineering و هدف‌گیری deployment کم‌هزینه و قابل نگهداری.
- Spec Kit تنها مالک workflow مربوط به SDD است.
- دامنه Phase 0 فقط آماده‌سازی workflow و پایه‌های lean محصول است؛ application در این فاز ساخته نمی‌شود.

## جهت supplied by product lead برای first slice

این موارد از prompt هماهنگ‌کننده Phase 1 آمده‌اند و finding حاصل از user research نیستند:

- category اولیه تلفن همراه و interface اولیه فارسی/RTL است.
- access به‌صورت guest-first و بدون account اجباری است.
- history در scope اولیه فقط در همان browser قابل دسترسی است؛ کاربر می‌تواند یک analysis یا تمام history
  خود را حذف کند.
- cross-device recovery و public report sharing در first slice وجود ندارد.
- intended product و approximate price به‌صورت دستی و با واحد تومان وارد می‌شوند.
- جهت اولیه questionnaire بازه ۵ تا ۸ core question و حداکثر سه conditional follow-up بود؛ اصلاح Phase 1.1
  آن را به شش core question و یک pool واحد حداکثر سه follow-up نهایی کرد.
- numeric score پیش از review rubric پیاده‌سازی نمی‌شود.
- mock AI فقط برای development/test است و real AI integration پیش از live-ready بودن MVP الزامی است.
- model name و price به‌تنهایی evidence مشخصات فنی، market value یا competitive price نیستند.

## تصمیم‌های product lead در Phase 1.1

این تصمیم‌ها مستقیماً از prompt اصلاح محصول آمده‌اند و finding پژوهشی نیستند:

- retention pilot برابر ۹۰ روز از اولین report persistشده و non-sliding است. visit، feedback، retry و edit
  همان analysis آن را reset نمی‌کنند؛ active-storage purge حداکثر ۲۴ ساعت پس از expiry هدف‌گذاری می‌شود.
- categorical outcome برای first slice پذیرفته است. Purchase Fit Score عددی حذف نشده و deferred می‌ماند.
- provider/model و request/token/cost limits به AI integration موکول می‌شوند؛ real provider، limits صریح و
  evaluation شرط live readiness هستند.
- usefulness feedback حداقلی و اختیاری ۱ تا ۵ به first slice بازگشته است؛ rating متعلق به report revision و
  mode جاری است و dashboard/SDK analytics در scope نیست.
- justification خرید/تعویض، budget fit و suitability مدل هدف باید conclusionهای مستقل باشند؛ unknown مدل
  نباید conclusionهای supported دیگر را حذف یا از طریق wording مثبت شود.

## تصمیم‌های product lead در Phase 2

- rubric `PDA-CAT-v0.3` پس از حذف strong/moderate مبهم، تعریف justification total و جدول ordered outcome
  برای technical planning پذیرفته است؛ implementation مجاز نشده است.
- صرف noted بودن repair/wait evidence feasibility یا preference نیست و positive justification را override
  نمی‌کند. `RECONSIDER_OR_WAIT` به evidence صریح مثل `NO_CLEAR_BENEFIT` یا target mismatch نیاز دارد.
- همه inputهای valid دقیقاً یک primary outcome و statusهای مستقل budget/justification/target-fit/tradeoff دارند؛
  contradiction/unknown justification قبل از positive outcome و above-budget قبل از همه headlineهاست.
- direction فنی plan: React + TypeScript + Vite، Django + DRF، PostgreSQL، modular monolith تک-repository،
  Docker Compose، static frontend production build، same-origin و small single-server deployment.

## اصلاحات فنی مصوب Phase 3

- unsafe APIهای guest anonymous با `CsrfViewMiddleware` و `csrf_protect` صریح Django محافظت می‌شوند؛ اتکا به
  `SessionAuthentication` برای CSRF مهمان مجاز نیست.
- lifecycle هر analysis همچنان ۹۰روزه و non-sliding است، اما persist یک analysis جدید access/session lifetime مهمان
  را تا expiry همان analysis تمدید می‌کند. visit/edit/retry/feedback تمدیدکننده نیستند.
- `GuestContext.generation_epoch`، initial create را با clear-history serialize می‌کند و operation token هر analysis
  فقط تازه‌ترین edit/retry روی همان revision را مجاز به publish می‌کند؛ network داخل transaction نیست.
- mock report mode برابر `MOCK_ASSISTED` است؛ `AI_ASSISTED_SUCCESS` فقط provider واقعی و metric آن مستقل است.

## مجوز و closure رابط در Phase 4

- M1 backend برای integration پذیرفته است و فقط M2 با شناسه‌های `T026`, `T027`, `T030`, `T033`, `T034`
  مجاز شده؛ M3 live AI و M4 production/deployment باز و بدون مجوز implementation می‌مانند.
- frontend همان React + TypeScript + Vite و API same-origin را مصرف می‌کند؛ Next.js، SSR، Vercel service،
  localStorage persistence و business-rule engine موازی رد شده‌اند.
- triggerهای M2 ثابت‌اند: `F-001` برای serious/contradiction به‌عنوان evidence تکمیلی، `F-002` فقط برای
  `Q-002=UNKNOWN` با mapping صریح به پاسخ نهایی Q-002، و `F-003` برای usageهای critical. ترتیب `F-001..003`
  و سقف کل سه است؛ unknown urgency به‌تنهایی clarification بی‌اثر ایجاد نمی‌کند.

## تصمیم‌های Phase 5 — M3

- گزینه‌های live کم‌هزینه به دو مورد محدود شدند: OpenAI `gpt-6-luna` و Google `gemini-3.5-flash-lite`. هر دو
  structured output دارند؛ quality فارسی و latency هیچ‌کدام هنوز در این workspace اندازه‌گیری نشده است.
- انتخاب مشروط: OpenAI Responses API با `gpt-6-luna`، SDK رسمی Python `3.49.0`، `store=false`، prompt
  `PDA-EXPLAIN-P1` و schema `PDA-EXPLAIN-v1`. دلیل: هزینه list پایین‌تر، structured output، multilingual capability
  مستند و کنترل application-state. alias snapshot جداگانه‌ای در catalog رسمی فعلی ارائه نمی‌کند؛ model ID صریح و
  configurable است و تغییر provider/model نیازمند decision/evaluation تازه خواهد بود.
- activation فقط وقتی مجاز است که محل backend و کاربران در region پشتیبانی‌شده باشد، `OPENAI_API_KEY` فقط در
  environment backend تنظیم شود و budget ارزیابی صریح وجود داشته باشد. ایران در فهرست فعلی OpenAI و Gemini نیست؛
  بنابراین timezone یا وجود key به‌تنهایی مجوز activation نیست.
- defaultها: live mode خاموش، timeout هشت ثانیه، حداکثر دو attempt فقط برای timeout/connection/408/409/429/5xx،
  output حداکثر ۵۱۲ token، request UTF-8 byte bound معادل upper-bound محافظه‌کار token، ۱۰ generation برای هر guest
  در روز، budget سراسری پیش‌فرض `$1.00/day` و circuit پنج failure متوالی برای پنج دقیقه. همه configurable هستند.
- evaluation spending cap هیچ default پولی ندارد و باید صریح تنظیم شود. reservation PostgreSQL هزینهٔ بدبینانه همه
  attemptها را قبل call نگه می‌دارد تا concurrency یا retry ceiling را دور نزند؛ provider invoice authoritative است.
- validation فقط schema، outcome/unknown echo، IDها و سازگاری claim/evidence/rule را تضمین می‌کند. وجود evidence ID
  اثبات semantic support متن فارسی نیست؛ این ریسک در evaluation مستقل و review انسانی باقی می‌ماند.

## اصلاحات Phase 5.1 — verified AI review

- headline، arithmetic و reasonهای پایه deterministic شدند؛ AI فقط explanation تکمیلی supplied context است.
  suitability مثبت فقط با value صریح `USER_REPORTS_IT_FITS` و attribution کاربر پذیرفته و همچنان user-reported است.
- semantic entailment متن آزاد، عدد/alternative ساختگی و headline متناقض با blacklist یا LLM judge خودکار اعلام
  نمی‌شود؛ این‌ها در artifact انسانی `pending/null` می‌مانند.
- dataset `PDA-AI-EVAL-v1.1` هفت case با expected outcome/unknown مستقل، رقم فارسی واقعی و contradictory-input دارد.
  artifact محلی synthetic مجاز است؛ real input، credential و raw transport ممنوع‌اند.
- قیمت رسمی `gpt-6-luna` در 2026-11-14 دوباره تأیید شد. estimator مشترک instructions/input/schema/framing
  margin/output/all attempts را رزرو می‌کند؛ observed usage clip نمی‌شود و settlement تکراری idempotent است.
- ساختار و visual language رابط حفظ شد؛ copy طبیعی‌تر، summary mobile یک card چهارردیفی و endpointهای feedback
  برای screen reader صریح شدند. هیچ M4 یا live call مجاز/اجرا نشد.

## پیش‌فرض‌های Phase 0 که در Phase 2 مصوب شدند

React + TypeScript + Vite، Django REST Framework، PostgreSQL، monorepo modular monolith، Docker Compose،
static frontend production build و deployment مناسب یک سرور کوچک با direction صریح Phase 2 از حالت proposed
خارج شدند. version baseline و rationale آن‌ها در `research.md` و معماری در `plan.md` ثبت است. Phase 4 مجوز
scaffold و implementation فقط برای M2 را می‌دهد؛ production deployment همچنان مجاز نیست.

## فرض‌های اعتبارسنجی‌نشده

- مخاطب اولیه فارسی‌زبانِ مردد برای خرید یا تعویض تلفن همراه است.
- مناسب‌بودن محدودیت category به تلفن همراه باید با product usage واقعی validate شود.
- ورود دستی مدل/قیمت و same-browser history باید از نظر usability و ارزش بازگشت validate شوند.
- نمایش score و indicator کیفی برای کاربر مفید و قابل فهم خواهد بود.
- history و usefulness feedback ارزش کافی برای حضور در MVP دارند.

## پرسش‌های باز

1. backup retention/erasure lifecycle پیش از production readiness در فاز deployment چه خواهد بود؟
2. **بسته‌شده در Phase 5.2:** backend/کاربران ایران و cap کل ۱۰۰٬۰۰۰ تومان تأیید شد. eligibility/upstream AvalAI،
   credential و credit محلی همچنان gateهای باز live evaluation هستند.

questionnaire، rubric، feedback و retention lifecycle در `specs/001-purchase-decision-analysis/` مستند شده‌اند.
تایید specification با اجرای implementation یکی نیست.

## تصمیم‌های Phase 7 — Shopping Copilot

- direction جدید product lead یک shopping copilot شخصی، conversation-first و چنددسته‌ای با bounded research و
  Choice Desk Concept 2 است. feature canonical تازه `002-personalized-shopping-copilot` است و feature 001 overwrite
  نمی‌شود.
- milestoneها A conversation، B evidence/source، C Choice Desk، D memory/OpenAI readiness و E operations/pilot gate
  هستند. Phase 7 planning-only است؛ همه taskهای implementation باز می‌مانند.
- stack و topology موجود حفظ می‌شود. SSE transport پیشنهادی برای server-to-browser event است؛ WebSocket/queue فقط
  با نیاز اندازه‌گیری‌شده و تصمیم تازه مجاز است.
- پژوهش فقط on-demand و bounded است. robots observation، terms، response واقعی، extraction، variant identity،
  freshness و rate/size limits per domain gate جدا دارند؛ timeout یا search snippet permission/extraction نیست.
- direct OpenAI Responses تنها runtime AI feature 002 است و fallback به AvalAI ندارد. user-owned key secret/billing
  ownership را تعیین می‌کند اما با users/backend ایران، region eligibility فعلاً تأیید نشده و live activation fail
  closed می‌ماند. Phase 7 live call و provider cost ندارد.
- memory default-off است؛ فقط preference تأییدشده reusable می‌شود. candidate inference و context self/gift/household
  جدا هستند. credential فقط backend-side، encrypted/masked/deleteable است؛ library/key operations در milestone D
  پس از evaluation انتخاب می‌شود.
- `COPILOT-RANK-v0.1` direction قطعی hard filter، total cost، versioned criteria، explicit missing evidence و stable
  ties را تعریف می‌کند. LLM fact/price/arithmetic/rank authoritative نمی‌سازد.
- retention entityهای جدید هنوز تصمیم نهایی نیست. 90 روز conversation فقط proposal در data model است و قبل از
  implementation نیازمند privacy/backup decision است؛ policy feature 001 خودکار تعمیم نمی‌یابد.
- T039 feature 001 و public/live gates با specification جدید complete نمی‌شوند. cutover/legacy retirement تصمیم‌های
  جدا و reversible هستند.

## تصمیم‌های هماهنگ‌کنندهٔ Phase 8 — Milestone A

- conversation، message و brief جاری 90 روز پس از آخرین user message پذیرفته‌شده یا brief edit/confirmation منقضی
  می‌شوند. read/list/SSE/replay/automatic retry/generator/background anchor را تمدید نمی‌کنند.
- upload حداکثر 24 ساعت از creation و stream event برابر 24 ساعت retention دارد. replay ناموجود از REST reconcile
  می‌شود و regeneration نمی‌کند. purge command bytes/rows expired را حذف می‌کند؛ backup erasure فوری وعده داده نمی‌شود.
- guest access با eligible action تا آخرین conversation expiry owned تمدید می‌شود؛ browser credential loss recovery
  ندارد. feature 001 expiry بدون تغییر است و cleanup نباید owner دارای conversation فعال را حذف کند.
- executor کوچک process-local فقط fixture را پس از transaction commit اجرا می‌کند و با PostgreSQL lease/claim مشترک
  هماهنگ می‌شود. crash/restart operation را `INTERRUPTED` می‌کند و خودکار restart نمی‌کند. SSE reader execution را
  start نمی‌کند و explicit cancel مستقل از connection است.
- M1/A فقط shell گفت‌وگو، brief قابل‌ویرایش، upload محافظت‌شده، streaming واقعی fixture و Desk readiness خالی را
  پیاده می‌کند. product/price/review/ranking/citation و merchant offer ساختگی ممنوع و Milestone C زودهنگام نیست.

## تصمیم‌های Phase 9 — Milestone B evidence foundation

- research فقط با trigger صریح و brief تأییدشده شروع می‌شود؛ default runtime برابر `OFFLINE` است. `FIXTURE` فقط
  evidence مصنوعی و label‌شده می‌سازد و شکست `LIVE` هرگز به fixture fallback نمی‌کند.
- حدود اولیهٔ مصوب: ۳ domain/job، ۵ content page/domain، ۲ redirect/request، ۲۰ HTTP request/job، ۲ MiB decoded/page،
  ۲۰ ثانیه/request، ۶۰ ثانیه/job، concurrency خروجی ۲/process، یک job فعال/guest و pace حداقل ۱ ثانیه/domain است.
  semaphore process-local deployment-global نیست؛ source policy سخت‌گیرانه‌تر اولویت دارد و retry نامحدود وجود ندارد.
- transport فقط HTTP(S) و port/path/host allowlist را می‌پذیرد؛ همهٔ DNS answerها باید public باشند و connection
  واقعی به IP تأییدشده pin می‌شود، در حالی که TLS hostname verification و Host اصلی حفظ می‌شوند. proxy محیطی، cookie،
  credential، browser/CAPTCHA bypass و private endpoint مجاز نیست.
- raw response حداکثر ۲۴ ساعت و بدون sliding expiry نگه‌داری می‌شود. evidence نرمال‌شده بیشتر از conversation مالک
  عمر نمی‌کند. retrieval timestamp روی cache hit تغییر نمی‌کند؛ freshness offer از retention cache جداست.
- probe موفق، extraction موفق و permission/enablement سه gate مستقل‌اند. در ۲۰۲۶-۱۱-۱۵ Philips و Technolife
  extraction حداقلی موفق داشتند ولی permission/retention/display برای این integration روشن نبود؛ Torob فقط policy
  probe شد و Apple/adidas/Decathlon برای automated retrieval مناسب نبودند. بنابراین allowlist live فعلاً خالی و همهٔ
  sourceها disabled هستند. sports fixture و Iranian current offer باز می‌مانند؛ cheapest/current-market ادعا نمی‌شود.
- evidence entityهای `SourcePolicy`, `ResearchJob`, `SourceSnapshot`, `EvidenceClaim`, `Product`, `Variant`, `Offer`
  با migration غیرمخرب افزوده شدند و research lifecycle از `StreamOperation`/`StreamEvent`، lease و lock order موجود
  استفاده می‌کند. Milestone C ranking، memory، credential، provider call، public deployment و هر دو T039 خارج scope‌اند.

## اصلاحات Phase 9.1 — bounded research pipeline

- LIVE input یک domain discovery نیست؛ target شامل source policy hostname و exact product URL است. fixture می‌تواند
  URL-null بماند. idempotent replay به payload/revision اصلی وفادار است و brief تازه آن را reinterpret نمی‌کند.
- acceptance زیر Guest→Conversation lock مالکیت، expiry، confirmation، expected revision، target association و
  guest-wide admission را یک‌جا می‌سنجد. boolean revision و object/list malformed با 422 رد می‌شوند.
- network/extraction بیرون transaction است. publication پس از revalidation lease/cancel/expiry/revision/generation و
  current source policy، snapshot/product/variant/offer/claims، counters و eventها را اتمیک commit می‌کند؛ cache همان
  guard را دارد.
- `FetchBudget` persisted limits را اجرا می‌کند: DNS/pacing/capacity/connect/TLS/header/body deadline، request/domain/
  redirect budget، wire/decoded size، gzip کامل و path normalized. شمارنده‌های مصرف واقعی روی failure نیز حفظ می‌شوند.
- controlled localhost server فقط test connector است؛ DNS/public-IP validation production دور زده نمی‌شود. این test
  plumbing را verify می‌کند، نه permission یا کیفیت source عمومی. enabled public policy همچنان صفر است.

## تصمیم‌های Phase 5.2 — provider ایران

- context قطعی: کاربران اولیه و backend در ایران هستند؛ قیمت و بودجهٔ خرید همچنان تومان است.
- direct OpenAI برای این deployment approved نیست. adapter مستقیم و region confirmation آن غیرفعال می‌ماند؛
  base URL سفارشی قرارداد یا eligibility آن را تغییر نمی‌دهد.
- shortlist به AvalAI و Liara محدود شد. AvalAI به‌عنوان تنها candidate انتخاب شد؛ Liara برای model بررسی‌شده
  Structured Outputs را غیرفعال و پلن پایه را ۲۹۹هزار تومان اعلام می‌کند.
- قرارداد انتخابی AvalAI Responses API، مدل دقیق `gpt-5.6-luna`، schema strict، `store=false`، timeout ۸ ثانیه،
  حداکثر دو attempt transient و usage/request-id provider است. OpenAI-compatible بودن مبنای Responses support نیست؛
  endpoint Responses در مستندات خود AvalAI آمده است.
- تعرفهٔ ثبت‌شده در 2026-11-14: input `$5/M`، cached input `$0.5/M` و output `$30/M`. User API نرخ جاری
  IRT-per-UNIT را می‌دهد؛ IRT در قرارداد AvalAI تومان است. reservation با margin ارزی ۱۵٪ انجام می‌شود و پول AI
  از `price_toman`/`budget_toman` خرید جدا است.
- سقف کل evaluation اولیه، همراه retry، دقیقاً ۱۰۰٬۰۰۰ تومان است. این سقف مجوز subscription/top-up/registration
  یا infrastructure نیست. command علاوه بر cap محلی، credential، credit/rate تازه و eligibility را fail closed می‌کند.
- unresolved: AvalAI در policy خود عدم بهره‌برداری از API data را می‌گوید، اما authorization و data path/retention
  upstream برای کاربران ایران را مستند نکرده است. همچنین مصرف signup grant برای همین model بدون base top-up باید از
  `/credit` یا پاسخ provider تأیید شود. تا آن زمان production activation و live evaluation eligible تلقی نمی‌شوند.
- T039 فقط پس از artifact live هفت case و review انسانی کامل می‌شود؛ test stub یا output ساختاری به‌تنهایی کافی نیست.

## اصلاحات Phase 5.3 — accounting و evaluation

- cap روزانهٔ deployment و authorization کل evaluation دو تصمیم مستقل‌اند؛ command حق جایگزین‌کردن اولی با دومی را ندارد.
- allowance اولیهٔ ۱۰۰٬۰۰۰ تومان یک authorization پایدار است، نه budget روزانه/هر process. spent و outstanding reservation
  در PostgreSQL across restart، concurrency و midnight حفظ می‌شوند.
- rejection پیش از provider call evidence یک call نیست: attempt/token/cost صفر و reason ساختاریافته دارد و run را ناقص نگه می‌دارد.
- usage هر attempt جدا حساب می‌شود؛ known usage clip نمی‌شود و unknown attempt allowance محافظه‌کارانه می‌گیرد.
  reserved underflow integrity error است و recovery رهاشدگی invoice قطعی ادعا نمی‌کند.
- policy `PDA-AI-EVAL-v1.2` spend authorization، structural، latency، human و product cost target را جدا می‌کند.
  output سهم worst-case reservation مدل منتخب در سقف ۵۱۲ token برابر `$0.01536` و بالاتر از target تاریخی
  `$0.0025/generation` است؛ این ریسک، observed average نیست و به‌تنهایی ناممکن‌بودن average را ثابت نمی‌کند.
  threshold relax نمی‌شود و observed product cost تا live evidence pending می‌ماند.

## اصلاحات Phase 6.1 — production configuration

- image پین‌شدهٔ PostgreSQL 18.1 مقدار `PGDATA=/var/lib/postgresql/18/docker` و image volume برابر
  `/var/lib/postgresql` دارد؛ named volume production از `/var/lib/postgresql/data` به parent رسمی اصلاح شد. صحت فقط
  با metadata، `SHOW data_directory`، mount inspection و container recreation با volume حفظ‌شده پذیرفته می‌شود.
- production AI default همچنان `mock` است. همهٔ non-secretهای AvalAI صریح map می‌شوند و live credential فقط از
  `compose.production.live.yaml` و file secret وارد می‌شود؛ direct OpenAI region flag و production test controls صفرند.
- health probe از `BEFOREBUY_HEALTHCHECK_HOST` صریح استفاده می‌کند. این host باید بدون wildcard عضو
  `DJANGO_ALLOWED_HOSTS` باشد؛ `Host: localhost` ثابت یا تضعیف host validation پذیرفته نیست.
- rehearsal Phase 6.1 محلی و synthetic است؛ هیچ provider call، deployment عمومی یا تغییر gateهای T039 انجام نشد.

## اصلاحات Phase 6.2 — development environment

- PostgreSQL توسعه با همان image digest پین‌شدهٔ 18.1 باید named volume را روی parent رسمی
  `/var/lib/postgresql` mount کند؛ portهای قابل‌تنظیم API و database فقط روی `127.0.0.1` منتشر می‌شوند.
- data موجود فقط با توقف write، dump منطقی محافظت‌شده، restore در named volume تازه و مقایسهٔ
  row/ownership/session/accounting منتقل می‌شود. source anonymous volume، named volume قدیمی و backup برای rollback
  حفظ می‌شوند؛ حذف volume یا restore روی volume فعال مجاز نیست.
- فرمان canonical backend از ریشه `scripts/test-backend.sh` است و label `tests` را از working directory backend
  اجرا می‌کند تا با `tests/e2e` collision نداشته باشد. live AI، public release و `T039` با این اصلاح تغییری نمی‌کنند.

## Phase 9.2 — narrow real-offer pilot

- تصمیم narrow pilot با مجوز عمومی یا پوشش بازار یکی نیست: exact `/p/` ترب و exact product path سه direct merchant فقط با اقدام صریح کاربر، attribution، field minimization، raw retention حداکثر 24h، freshness 6h و pace حداقل 2s قابل فعال‌سازی‌اند. robots allowance/HTTP 200 به‌تنهایی permission نیست.
- دیجی‌کالا به‌خاطر شکست extraction پایدار خاموش می‌ماند، نه به ادعای منع حقوقی. sourceهای دارای منع صریح و همه search/account/cart pathها خاموش‌اند.
- قیمت original/currency از `price_toman` جداست؛ IRR فقط با `10 IRR = 1 TOMAN` تبدیل می‌شود و تعارض واحد fail closed است. shipping و mandatory charges نامعلوم صفر نیستند و total payable فقط با اجزای کامل ساخته می‌شود.
- مقایسه فقط variantهای compatible است؛ merchant SKU شناسهٔ بین‌فروشگاهی نیست. duplicate observation حذف نمایشی می‌شود ولی provenance/discrepancy خام باقی می‌ماند.
- default runtime همچنان `OFFLINE` است. فعال‌سازی policy و اجرای pilot commandهای صریح operator می‌خواهد؛ هیچ fixture، AI/provider، account، purchase یا public deployment در این تصمیم مجاز نیست.

## Phase 10 — bounded offline Choice Desk

- مجوز فقط T024–T031 است. evidence models و fixture کنترل‌شده dependency اجرای C را تأمین می‌کنند؛ موفقیت public extraction فقط gate پوشش زنده است. Milestone B، T066 و T039 کامل محسوب نمی‌شوند.
- closure اجرایی COPILOT-RANK-v0.1 دسته‌ای/lexicographic است: HARD/PREFERENCE، SATISFIED/FAILED/UNKNOWN، STRICT پیش‌فرض و FLEXIBLE فقط با تأیید، known total جدا از item price؛ بدون وزن یا امتیاز ساختگی.
- ترتیب: سازگار، حل‌نشده، ناسازگار؛ در هر گروه coverage سپس ترجیح‌های مستند؛ هزینهٔ کمتر فقط با ترجیح صریح. UUID صرفاً نمایش tie را پایدار می‌کند، نه winner ساختگی.
- معیار عددی equality است، نه حداقل استنباط‌شده. هدیه فقط معیار گیرنده را مصرف می‌کند؛ هدف لذت معتبر است؛ هیچ تشخیص روانی/مالی انجام نمی‌شود. تناقض brief و شرط متنی حل‌نشده مانع winner قطعی‌اند.
- ChoiceSet immutable JSON با itemهای embedded، revision/epoch و freshness است؛ owner/expiry/revision در publication زیر lock بازبینی می‌شود. retention و حذف از conversation ارث می‌رسند؛ read/compare/demo تمدید نمی‌کنند.
- نمونه‌های صریح سه دسته در Product/Variant/Offer/Claim عادی ذخیره و از همان API/engine/UI مصرف می‌شوند. synthetic/captured به بازار فعلی یا VERIFIED_SOURCE ارتقا نمی‌یابند. بارگذاری نمونه نیاز تأییدشده را تغییر نمی‌دهد.
- یک محصول موردنظر + حداکثر سه محصول جایگزین؛ merchant offerها جدا. memory، credential settings، provider و deployment خارج این فازند. پوشش live بازار و AI همچنان باز است.
