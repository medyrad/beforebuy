# Feature Specification: دستیار شخصی خرید

**Feature Branch**: `002-personalized-shopping-copilot`

**Created**: 2026-11-15

**Status**: Settings correction T093–T095/T097 authorized after bounded UX T086–T092; T096/free-provider integration and live/public gates remain pending

**Input**: تبدیل Beforebuy از پرسش‌نامهٔ تلفن به دستیار گفت‌وگومحور چنددسته‌ای با پژوهش محدود، میز انتخاب، حافظهٔ opt-in و credential مجزای provider متعلق به کاربر.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - روشن‌کردن تصمیم در گفت‌وگو (Priority: P1)

کاربر فارسی‌زبان مسئلهٔ خرید را با متن و در صورت نیاز تصویر مطرح می‌کند. دستیار با کمترین سؤال consequential، نیاز، بودجه، کاربرد، محدودیت سخت، مخاطب خرید و uncertainty را روشن می‌کند و بدون تشخیص روان‌شناختی یک brief قابل بازبینی می‌سازد.

**Why this priority**: بدون brief معتبر، پژوهش و رتبه‌بندی ظاهراً دقیق اما نامرتبط خواهد بود.

**Independent Test**: با fixture آفلاین و بدون provider، گفت‌وگوی چندمرحله‌ای باید brief نسخه‌دار، budget/constraintهای قطعی و unknownهای صریح تولید کند.

**Acceptance Scenarios**:

1. **Given** کاربر می‌گوید «برای خودم لپ‌تاپ می‌خواهم تا ۷۰ میلیون»، **When** کاربرد و محدودیت‌های مهم را پاسخ می‌دهد، **Then** brief واحد پول، سقف بودجه، self-context، نیازها و unknownها را جدا نشان می‌دهد.
2. **Given** خرید هدیه است، **When** preference گیرنده معلوم نیست، **Then** context هدیه با preference شخص کاربر ادغام نمی‌شود و unknown باقی می‌ماند.
3. **Given** متن یا تصویر شامل ادعای محصول است، **When** source مستقل نداریم، **Then** ادعا user-provided یا unverified ثبت می‌شود و fact قطعی نیست.

---

### User Story 2 - پژوهش محدود و قابل‌ردیابی (Priority: P1)

کاربر می‌تواند برای brief تأییدشده پژوهش on-demand را آغاز، progress واقعی را ببیند و آن را لغو کند. محصول فقط از sourceهای مجاز و bounded داده می‌گیرد و هر fact، قیمت، variant و زمان مشاهده را با citation نشان می‌دهد.

**Why this priority**: recommendation چنددسته‌ای بدون evidence تازه اعتمادپذیر نیست.

**Independent Test**: سه category fixture (electronics، home appliance، sports/fashion) باید policy، limit، dedupe، cancellation، extraction و failure صریح را بدون شبکه تست کنند.

**Acceptance Scenarios**:

1. **Given** یک manufacturer page و یک merchant offer مجاز، **When** research اجرا می‌شود، **Then** مشخصات سازنده از قیمت/availability فروشنده و زمان retrieval جدا می‌شوند.
2. **Given** CAPTCHA، login، paywall، robots restriction یا timeout، **When** source قابل دریافت نیست، **Then** bypass انجام نمی‌شود و coverage gap آشکار می‌ماند.
3. **Given** دو variant با شناسه یا مشخصات ناسازگار، **When** identity حل نمی‌شود، **Then** قیمت یا review میان آن‌ها merge نمی‌شود.
4. **Given** کاربر cancel می‌کند، **When** کار در حال fetch/extract است، **Then** کار جدید آغاز نمی‌شود، نتیجهٔ دیررس publish نمی‌شود و وضعیت cancelled قابل مشاهده است.

---

### User Story 3 - مقایسه در Choice Desk (Priority: P1)

کاربر shortlist را در «میز انتخاب» می‌بیند: cards و جدول تطبیقی responsive با fit، total payable cost، tradeoff، concern، evidence coverage و unknown. رتبه‌بندی فقط از ruleهای نسخه‌دار و preferenceهای تأییدشده می‌آید.

**Why this priority**: خروجی باید تصمیم را قابل مقایسه کند، نه صرفاً متن بیشتری تولید کند.

**Independent Test**: یک dataset ثابت باید ترتیب، tie، hard-filter، missing evidence و explanation یکسان را در API و UI تولید کند.

**Acceptance Scenarios**:

1. **Given** گزینه‌ای از budget یا compatibility قطعی خارج است، **When** رتبه‌بندی می‌شود، **Then** hard filter آن را حذف/هشدار می‌دهد و LLM نمی‌تواند آن را اول کند.
2. **Given** evidence دو گزینه ناکامل است، **When** امتیاز subjective نمایش داده می‌شود، **Then** coverage و uncertainty کنار fit دیده می‌شود و precision ساختگی ندارد.
3. **Given** قیمت پایه و هزینهٔ ارسال/لوازم لازم موجود است، **When** total payable cost محاسبه می‌شود، **Then** arithmetic قطعی با تومان و provenance هر جزء نمایش می‌یابد.

---

### User Story 4 - پاسخ و progress به‌صورت stream واقعی (Priority: P2)

کاربر deltaهای پاسخ و eventهای واقعی research را بدون refresh دریافت می‌کند؛ می‌تواند stop کند و پس از قطع اتصال state نهایی authoritative را دوباره بخواند.

**Why this priority**: انتظار طولانی گفت‌وگو/پژوهش باید قابل فهم باشد، ولی streaming نباید حقیقت یا correctness را تضعیف کند.

**Independent Test**: stream fixture باید ordering، reconnect، cancellation، error، duplicate event و stale publication را با event IDs ثابت بررسی کند.

**Acceptance Scenarios**:

1. **Given** پاسخ در حال تولید است، **When** delta می‌رسد، **Then** به‌عنوان provisional نمایش داده می‌شود و فقط event نهایی validated به message قطعی تبدیل می‌شود.
2. **Given** اتصال قطع می‌شود، **When** کاربر برمی‌گردد، **Then** state از API خوانده می‌شود و event تکراری پیام را دو بار نمی‌سازد.
3. **Given** screen reader فعال است، **When** deltaهای سریع می‌رسند، **Then** اعلان‌ها throttled و قابل توقف‌اند و focus ربوده نمی‌شود.
4. **Given** budget قبلاً در brief ثبت شده، **When** کاربر دربارهٔ مقایسه سؤال می‌کند، **Then** دستیار budget را دوباره نمی‌پرسد و پاسخ از ChoiceSet جاری استفاده می‌کند.
5. **Given** کاربر می‌پرسد «چرا گزینه دوم؟»، **When** ChoiceSet جاری و evidence معتبر وجود دارد، **Then** tradeoff همان candidate با attribution و uncertainty توضیح داده می‌شود؛ ranking تغییر نمی‌کند.
6. **Given** evidence فنی کافی نیست، **When** پاسخ ساخته می‌شود، **Then** unknown و راه بررسی صریح نمایش داده می‌شوند و product claim یا alternative ساخته نمی‌شود.

---

### User Story 5 - حافظه و کلید تحت کنترل کاربر (Priority: P2)

کاربر می‌تواند preferenceهای مشخص را opt-in ذخیره، مشاهده، اصلاح یا حذف کند و کلید OpenAI خود را به‌صورت masked مدیریت کند. temporary conversation و candidate inference خودکار حافظهٔ دائمی نیستند.

**Why this priority**: شخصی‌سازی و هزینهٔ user-owned بدون consent، deletion و secret safety قابل قبول نیست.

**Independent Test**: consent، isolation، encrypt/decrypt boundary، masking، deletion، rotation و region gate با credential synthetic بررسی می‌شوند و هیچ تماس live لازم نیست.

**Acceptance Scenarios**:

1. **Given** memory خاموش است، **When** preference در گفت‌وگو بیان می‌شود، **Then** خارج از retention گفت‌وگو به profile منتقل نمی‌شود.
2. **Given** یک inferred candidate وجود دارد، **When** کاربر آن را تأیید نکرده، **Then** recommendation آینده آن را preference قطعی تلقی نمی‌کند.
3. **Given** key ذخیره شده، **When** UI یا log نمایش می‌دهد، **Then** plaintext هرگز برنمی‌گردد و replace/delete ممکن است.
4. **Given** کاربر/backend در ایران است، **When** فقط key وارد شده، **Then** live activation تا eligibility مستقل provider/model و مجوز هزینه blocked می‌ماند.
5. **Given** کاربر می‌گوید «گوشی من شکسته می‌خواهم آیفون ده بخرم»، **When** provider منتخب و مجاز پاسخ می‌دهد، **Then** دستیار گفتهٔ کاربر را می‌فهمد، یک ابهام consequential را طبیعی می‌پرسد و ادعای قیمت/مشخصات جاری نمی‌سازد.

### Edge Cases

- budget unknown، صفر، بازه‌ای، چندارزی یا با رقم فارسی/لاتین؛ shipping/mandatory accessory نامعلوم.
- خرید برای self، gift یا household و تغییر context وسط conversation.
- تصویر بزرگ/نامعتبر/حاوی metadata یا متن prompt-like؛ فایل حذف‌شده در جریان generation.
- source تغییرکرده، قیمت stale، variant bundle/گارانتی متفاوت، duplicate URL و redirect بین domainها.
- robots/terms مبهم، 403/429/5xx، CAPTCHA، paywall، response بسیار بزرگ یا content-type غیرمنتظره.
- optionهای مساوی، evidence ناقص، preferenceهای متناقض و تغییر brief پس از research.
- disconnect، reconnect، event تکراری/خارج ترتیب، cancel هم‌زمان با completion و response دیررس.
- key نامعتبر/حذف‌شده/rotated، cap هزینه، provider error و region unsupported.
- حذف conversation هم‌زمان با research یا stream؛ دادهٔ cache مشترک نباید ownership خصوصی را افشا کند.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-082**: Authorized UX cutover MUST make `/` and `/copilot` conversational entry points, auto-create on first message, and preserve `/legacy` plus existing `/?analysis=` and history links without changing legacy data/API.
- **FR-083**: Concept 2 MUST use warm neutral surfaces, restrained indigo/teal, self-hosted Persian typography, right-hand conversation and progressive left-hand need/candidates/comparison/offers. Category shortcuts are prompts, not coverage claims. Independent thread scrolling MUST keep composer/stop reachable at 1440×900, 1280×720, 390×844, 360×640, reduced height and 200% zoom; auto-follow only near bottom.
- **FR-084**: Optional 2–5 server-owned reply actions MUST bind conversation, final question message and brief revision, use normal message/idempotency submission, show the answer and reject stale/foreign actions. Free text remains available; actions never trigger research or purchases.
- **FR-085**: Explicit single-amount budget statements MUST retain user-reported attribution separately from confirmation. Conflicting amounts MUST remain proposals until confirmed/corrected in chat. `۱۵ میلیون ریال` after `بودجه‌ام ۱۵ میلیون تومان است` MUST propose 1,500,000 toman while retaining 15,000,000; 10 rial = 1 toman. This bounded parser is not general language understanding.
- **FR-086**: History MUST support loaded-title search, dates, pagination, new/open/delete/clear with confirmation and lifecycle disclosure. Switching MUST detach subscriptions/timers and guard late responses; drafts, scroll and research state are conversation-scoped. Credentials/independent preferences remain unchanged.
- **FR-087**: Mode/provider/model/credential labels MUST use backend state, not imply validation from storage. No provider call, credential change, research activation or public deployment is authorized. Verification MUST include real NGINX journeys, screenshot inspection, accessibility and preserved legacy access; physical-device limitations remain explicit.

- **FR-090**: The bounded OpenRouter pilot supersedes informational-only scope only after an exact model/upstream route is established as suitable for Iranian users/backend. Review at most two current free text routes. Do not infer permission from availability or prohibition from absent documentation. No blocked placeholder integration. A future eligible implementation MUST preserve provider-bound encryption/context/validation, fixed endpoint, zero paid authorization/cap, separate explicit local free-test consent, at most ten total generation attempts including validation/retries, current zero pricing checks for every applicable charge, bounded tokens/time, no model/provider fallback or paid tools, honest errors/usage/cost evidence and synthetic-only testing. No privacy changes without consent; research OFFLINE.
- **FR-091**: Native provider/model/category selects and adjacent inputs/buttons MUST use existing self-hosted Vazirmatn with consistent control typography, RTL/focus and isolated Latin identifiers. Verify computed styles, keyboard selection/Escape/focus, touch emulation, long labels and 390/1440 viewport fit with before/after screenshots. OS-rendered popup and physical-device limits MUST be reported; no UI framework is required.

- **FR-076**: OpenAI exclusivity is withdrawn. Runtime MUST select one explicit documented provider/model without
  arbitrary base URLs, hidden fallback or provider-routing framework. OpenAI remains optional only where officially
  eligible. OpenAI-compatible syntax alone MUST NOT establish Responses support, upstream authorization or regional eligibility.
- **FR-077**: Phase 12 selected path MUST use GapGPT model `gapgpt-deepseek-v4.1-flash` through its documented fixed
  Chat Completions streaming endpoint. Provider/model identity, endpoint, protocol and tariff MUST be pinned. Since
  JSON Schema/tool output is not documented for this model, output MUST be bounded JSON text and MUST pass the existing
  server-owned answer/evidence contract before publication; missing usage consumes the conservative reservation.
- **FR-078**: Provider credentials MUST have an explicit provider association. Existing encrypted OpenAI credentials
  MUST remain unchanged and MUST NOT be read as another provider's key. Settings MUST distinguish NOT_CONFIGURED,
  STORED_UNVALIDATED, VALIDATION_FAILED/BLOCKED and VALIDATED; saving MUST make zero provider calls and authorize no spend.
- **FR-079**: A live model MAY produce a bounded natural Persian acknowledgement and one useful free-form next question
  from the current conversation. It MUST distinguish user-reported content, general guidance, validated evidence and
  unknown/stale facts. Product facts/prices/ranks remain server-owned; unsupported factual content MUST be rejected or omitted.
- **FR-080**: Conversational understanding MUST consume the bounded context/history and MUST NOT depend on fixed user
  sentence keys or keyword routing. The assistant MAY propose validated structured brief changes for explicit confirmation;
  it MUST NOT silently confirm or overwrite the brief. Market unavailability MUST still allow needs clarification with an explicit evidence limitation.
- **FR-081**: Live validation/evaluation MUST remain blocked until a locally configured credential, provider eligibility
  evidence, dated USD→toman conversion plus margin and an explicit hard total spending authorization are present. Prior
  AvalAI/OpenAI budgets or keys MUST NOT be reused. Actual call/retry/token/latency/cost and human quality review are required before `live-verified` wording.

- **FR-069**: Provider context MUST be assembled from the bounded recent conversation, current brief/confirmation/contradictions, current valid ChoiceSet and only its relevant provenance/freshness/unknown/cost fields, current message/eligible images and consented relevant confirmed memory. Temporary conversations MUST exclude memory; current explicit criteria override saved preferences. Raw source text and quoted instructions are untrusted data and MUST NOT control system instructions or ranking.
- **FR-070**: Context assembly MUST use deterministic byte/item budgets. Critical hard constraints, contradictions and uncertainty MUST NOT be silently truncated; if they or the minimum current comparison cannot fit, generation MUST return an explicit limited response without a provider call. Optional history truncation MUST be oldest-first and visibly represented in the provider payload.
- **FR-071**: Each generation MUST pin a non-secret context manifest and fingerprint covering the current turn, brief/generation revision, model-settings revision, current ChoiceSet/evidence snapshots, eligible uploads and included memory revisions. Final publication MUST reject deletion, expiry, edits, credential/model changes, a newer accepted turn, stale evidence or memory changes. The manifest MUST NOT duplicate message/profile/source prose.
- **FR-072**: The assistant answer contract MUST support comparison question, evidence-backed mismatch, candidate tradeoff, at most three supported alternatives, one consequential clarification, and explicit unknown/next-check guidance. Generated blocks MUST reference current candidate/criterion/evidence identities and pass value, attribution, freshness and variant checks before factual rendering. Unsupported blocks are omitted or replaced by an explicit limited explanation. Deterministic arithmetic, outcome, rank, product facts and source evidence remain authoritative.
- **FR-073**: Streaming MUST expose meaningful context-aware provisional text without raw JSON, hidden reasoning or unvalidated product claims. Validated blocks MAY stream after validation and only the final persisted message is authoritative. Provider output MUST NOT receive artificial typing delays; cancellation/replay/reconnect remain exactly-once. Free-form semantic validation limits MUST be disclosed.
- **FR-074**: Account model discovery MUST have a direct OpenAI SDK `models.list()` transport seam tested only with stubbed HTTP. Returned IDs MUST be intersected with the documentation capability/pricing catalog; IDs alone never establish capability. Settings/key reads and writes MUST make zero provider calls. A future explicit refresh MUST report blocked/error/unavailable-selection states and remain region/credential gated.
- **FR-075**: Development demonstration MUST use the real context assembler, worker, event ledger, publication boundary and UI with deterministic scripted responses labelled synthetic. It MUST cover practical supported alternative, enjoyment tradeoff and insufficient-evidence guidance without a production-accessible bypass or live provider/source call.

- **FR-065**: Assistant settings and «شناخت من» MUST be discoverable on desktop/mobile. Credential writes never validate or list models over the network; stored/unvalidated, failed, blocked and validated states are separate. Documentation catalog is explicitly account-unverified; disappearing models fail closed without substitution.
- **FR-066**: Development-only provisional retention MUST be configurable: candidates 7 days from creation, confirmed preferences 90 days from confirmation, credentials 30 days from save/replace; reads/edits do not renew these anchors. Source conversation deletion/expiry deletes derived memories. Disable stops reuse/proposals without deleting; clear/delete removes active records, not historical backups. Owner access expiry remains an upper bound. Public activation requires product review.
- **FR-067**: Temporary conversations MUST neither read nor write persistent preferences. Only explicit structured confirmed comparison criteria may become labelled candidates. Reuse requires an explicit action on an unconfirmed brief with revision checks, never overwrites a current criterion, and keeps self/recipient/household separate. Owner-scoped memory-only export does not complete T050.
- **FR-068**: Credential replacement/deletion MUST invalidate queued credential revisions. Runtime gates MUST reject unsupported deployment independently of stored keys or browser inputs. Existing AIInvocation/budget reservation infrastructure MUST enforce finite operation/session caps across retries, including unknown usage; no new accounting framework.

- **FR-063**: Milestone C MUST use confirmed structured comparison criteria and categorical COPILOT-RANK-v0.1 rules, compare one intended variant with at most three evidenced product alternatives, preserve unresolved/tied outcomes and expose criterion/evidence/tradeoff/unknown/coverage/would-change reasoning. Explicit enjoyment is valid and gift criteria belong to the recipient.
- **FR-064**: ChoiceSet MUST be owner-scoped, revision/epoch guarded and visibly invalidated by brief edits or stale evidence. Three labelled synthetic category demonstrations MUST use the same persisted evidence, ranking/API/UI path as future live evidence, without source/LLM calls or upgrading attribution.

- **FR-061**: Phase 9.3 connection fallback MUST use at most two distinct addresses from one fully public-validated DNS result, retain hostname TLS/SNI/Host, share request/job deadlines, close failed sockets and count each additional connection against existing request/domain budgets. Fallback is only before HTTP send; policy, HTTP and parser failures are not retried.
- **FR-062**: Source enable/disable MUST preserve real review timestamps; configuration changes are not observations. Diagnostics MUST distinguish fresh host/container/application responses from captured/tool content, use at most 30 outbound attempts, and restore explicit OFFLINE/disabled policies. T066 requires real extraction/publication and a fresh repeat.

- **FR-001**: محصول MUST تجربهٔ فارسی، RTL، responsive و accessible گفت‌وگومحور برای تصمیم خرید چند category ارائه کند؛ پوشش UI MUST NOT به معنی آمادگی data source هر category باشد.
- **FR-002**: کاربر MUST بتواند بدون account اجباری conversation بسازد، ادامه دهد و حذف کند؛ ownership با session server-side موجود یا مرز معادل اثبات‌شده enforce شود.
- **FR-003**: message ورودی MUST text و MAY یک یا چند image محدود باشد؛ type، size، count، metadata و retention فایل باید validation و disclosure صریح داشته باشند.
- **FR-004**: system MUST shopping brief نسخه‌دار شامل intent، self/gift/household context، category، budget/currency، use cases، hard constraints، preferences، unknowns و confirmation state بسازد.
- **FR-005**: assistant MUST فقط سؤال consequential لازم بپرسد؛ enjoyment، celebration، gift و self-reward انگیزهٔ مشروع‌اند و diagnosis/impulsivity تلقی نمی‌شوند.
- **FR-006**: budget، currency، total payable cost، compatibility و hard filter MUST deterministic، نسخه‌دار و قابل آزمون باشند؛ missing value MUST unknown بماند.
- **FR-007**: research فقط با action صریح کاربر و brief کافی MAY آغاز شود و MUST limits دامنه، page، redirect، byte، time، concurrency و total job داشته باشد.
- **FR-008**: source policy MUST allow/deny، robots observation، terms/access status، auth/CAPTCHA/paywall rule، freshness و contact/user-agent را per domain ثبت کند؛ bypass ممنوع است.
- **FR-009**: fetcher MUST در برابر SSRF از scheme/host/IP/redirect validation، DNS rebinding، private/link-local/metadata address و content-type/size abuse محافظت کند.
- **FR-010**: هر extraction MUST source URL canonical، retrieval time، content fingerprint، extractor version، field-level provenance و failure state داشته باشد.
- **FR-011**: manufacturer fact، merchant offer، editorial/review claim، user report و assistant inference MUST نوع‌های جدا باشند و بدون evidence merge نشوند.
- **FR-012**: variant identity MUST brand/model/identifier/attributes/bundle/region را reconcile کند؛ ambiguity MUST مانع ادغام price/review شود.
- **FR-013**: price/availability MUST observation زمان‌دار باشد؛ shipping، warranty، seller، required accessory و currency componentهای جدا و total payable cost فقط از componentهای معلوم محاسبه شود.
- **FR-014**: review aggregation MUST sample/source/date/measurement limits را نگه دارد و popularity یا rating فروشگاه را به quality قطعی تبدیل نکند.
- **FR-015**: ranking MUST ابتدا hard filters و سپس criterionهای نسخه‌دار را اعمال کند؛ weight/normalization/tie/missing-evidence rule و rationale per option قابل مشاهده باشد.
- **FR-016**: LLM MUST NOT product fact، price، availability، arithmetic، seller trust، compatibility، score، rank یا citation بسازد/override کند.
- **FR-017**: Choice Desk MUST shortlist cards، comparison view، budget/fit/tradeoff/concern/unknown و evidence coverage را نشان دهد و در mobile بدون scroll افقی ضروری قابل استفاده باشد.
- **FR-018**: هر claim قابل مشاهده MUST citation یا attribution `USER_REPORTED`, `DETERMINISTIC`, `VERIFIED_SOURCE`, `ASSISTANT_INFERENCE`, `SYNTHETIC`, `CAPTURED_FIXTURE` یا `UNKNOWN` داشته باشد. دو حالت fixture هرگز شاهد بازار جاری نیستند.
- **FR-019**: recommendation MUST توضیح دهد چرا، با کدام tradeoff، تحت چه uncertainty و چه evidence تازه‌ای تغییر می‌کند؛ هدف افزایش خرید یا budget نیست.
- **FR-020**: stream MUST event ID، operation ID، sequence، type، timestamp و payload version داشته باشد؛ provisional delta fact نهایی محسوب نمی‌شود.
- **FR-021**: stream MUST progress واقعی مرحله/تعداد bounded work را ارسال کند و MUST hidden chain-of-thought، progress جعلی یا secret منتشر نکند.
- **FR-022**: cancellation MUST cooperative باشد و publication با operation token/revision guard جلوی late/stale result را بگیرد؛ state نهایی از API authoritative است.
- **FR-023**: preference memory MUST default-off و opt-in باشد؛ explicit preference، inferred candidate و context موقت جدا و review/correct/delete/disable داشته باشند.
- **FR-024**: conversation، message، upload، research snapshot، memory، credential و cost record MUST purpose، retention، deletion و owner جدا داشته باشند؛ حذف فوری backup فقط در صورت policy اثبات‌شده ادعا شود.
- **FR-025**: user-owned provider key MUST فقط backend-side، encrypted at rest، masked، replaceable/deletable، provider-associated و از log/frontend/URL/Git/merchant request دور بماند؛ encryption key جدا از database نگه‌داری شود.
- **FR-026**: runtime AI feature MUST یک provider/model صریح داشته باشد و هیچ fallback پنهان یا arbitrary base URL نداشته باشد؛ direct OpenAI دیگر انحصاری نیست.
- **FR-027**: model MUST از allowlist capability catalog انتخاب شود؛ text/image input، structured output، streaming، tool support، context و pricing MUST برای model ID دقیق revalidate شوند و نام model به‌تنهایی capability نیست.
- **FR-028**: OpenAI request MUST `store=false`، timeout/cancellation، bounded input/output، schema validation، request ID/usage و cost estimate/settlement داشته باشد؛ Responses streaming و eventهای application از هم تفکیک شوند.
- **FR-029**: user key، credit یا subscription MUST region eligibility را ثابت نکند. با users/backend ایران live OpenAI MUST fail closed بماند تا policy رسمی و شرایط واقعی deployment پشتیبانی را تأیید کند.
- **FR-030**: ChatGPT subscription و OpenAI API billing MUST جدا توضیح داده شوند؛ هر call نیازمند consent هزینه، estimate با margin و cap per operation/session است و estimate تضمین invoice نیست.
- **FR-031**: offline fixtures MUST conversation، extraction، ranking و streaming را بدون network/provider پوشش دهند؛ mock/fixture MUST صریحاً غیرزنده باشد.
- **FR-032**: same-origin Django/React/PostgreSQL/Compose topology MUST حفظ شود؛ transport ترجیحی streaming SSE است مگر test نیاز دوطرفه‌ای ثابت کند، و proxy buffering/timeout/shutdown باید قابل آزمون باشد.
- **FR-033**: feature 001 MUST به‌عنوان legacy evidence حفظ شود؛ migration/cutover MUST reversible و stage-gated باشد و T039 قدیمی نه complete و نه شرط runtime جدید تلقی شود.
- **FR-034**: source expansion، model activation و public release MUST gate مستقل داشته باشند؛ موفقیت یک category/source یا fixture به سایر categoryها تعمیم داده نشود.
- **FR-035**: system MUST data export حداقلی conversation/brief/memory و delete path قابل آزمون ارائه کند؛ plaintext credential هرگز export نمی‌شود.
- **FR-036**: accessible stream MUST throttled announcements، pause/stop، reduced motion، keyboard/focus semantics و status غیررنگی داشته باشد.
- **FR-037**: در Milestone A، conversation/message/brief MUST پس از آخرین accepted user message یا explicit brief edit/confirmation تا 90 روز retained باشند؛ read/list/SSE/replay/generator/background این anchor را تمدید نکند. Upload و StreamEvent MUST به‌ترتیب حداکثر 24 ساعت از creation و 24 ساعت retained باشند و cleanup نباید owner دارای conversation فعال را حذف کند.
- **FR-038**: message submission MUST یک `Idempotency-Key` bounded بپذیرد؛ همان key و canonical payload همان operation را برگرداند و reuse با payload متفاوت conflict بدهد. GET و SSE MUST generation را start/restart نکنند.
- **FR-039**: Milestone A MUST فقط fixture generator صریح و deterministic را با executor محدود، PostgreSQL claim/lease، interruption terminal، cancellation مستقل و stale-publication guard اجرا کند؛ crash/restart durability تضمین نمی‌شود.
- **FR-040**: image upload MUST raw body حداکثر 5 MiB، حداکثر سه فایل فعال در هر conversation، dimension حداکثر 4096 در هر محور و 12MP را enforce، decoded JPEG/PNG/WebP را re-encode و metadata را حذف کند؛ SVG/HTML، multi-frame و decompression-bomb رد شوند و bytes فقط owner-scoped سرو شوند.
- **FR-041**: final publication MUST در یک transaction و با lock order ثابت `Conversation → StreamOperation`، اعتبار expiry/revision/cancel/lease-owner را دوباره بررسی کند و FINAL message، `assistant.message.final`، `operation.completed` و state `COMPLETED` را با هم commit یا همگی rollback کند؛ mutationی که زودتر commit شود برنده است و worker دیررس MUST NOT publish کند.
- **FR-042**: SSE MUST عمر connection حداکثر 45 ثانیه، heartbeat حداکثر هر 15 ثانیه، admission صریح حداکثر دو subscriber هم‌زمان در هر process و cleanup idempotent داشته باشد؛ expiry یا operation stale باید از state تازه و زیر lock reconcile و terminal/close شود و reconnect MUST generation را تکرار نکند.
- **FR-043**: replay MUST با `next_sequence` authoritative میان no-history، partial/all-purged history، latest و future sequence تمایز بگذارد؛ foreign/malformed ID با `INVALID_REPLAY_ID`، future با `INVALID_REPLAY_SEQUENCE` و هر gap لازم با `REPLAY_GAP` و REST reconciliation URL پاسخ داده شود. purge پس از شروع stream MUST control event غیرپایدار `stream.replay_gap` بدهد و client از REST بدون regeneration reconcile کند.
- **FR-044**: هر research job MUST فقط با trigger صریح اجرا شود و limits اولیهٔ مصوب آن حداکثر 3 domain، 5 content page در هر domain، 2 redirect در هر request، 2 MiB decoded در هر page، 20 ثانیه در هر request، 60 ثانیه wall time، 20 HTTP request کل و pacing حداقل 1 ثانیه per-domain باشد؛ retry، redirect و policy request همگی در budget حساب شوند. concurrency outbound حداکثر 2 در هر application process و active research job حداکثر 1 در هر guest است؛ process-local limit به‌عنوان deployment-global معرفی نشود.
- **FR-045**: readiness هر source MUST میان `SYNTHETIC_FIXTURE`, `CAPTURED_REAL_FIXTURE`, `LIVE_PROBE`, `REPEATABLE_LIVE_EXTRACTION` و `ENABLED` تفکیک شود. default application mode آفلاین است و live failure MUST NOT به fixture fallback کند؛ fixture price/availability دادهٔ جاری بازار نیست.
- **FR-046**: raw response cache MUST حداکثر 24 ساعت از retrieval و بدون sliding read expiry بماند؛ cache hit timestamp اصلی را حفظ کند. evidence خصوصی حداکثر تا lifecycle conversation مالک retained است؛ freshness per source مستقل از cache retention است و deletion/expiry فوراً publication را باطل و cleanup evidence خصوصی orphan و raw expired را purge می‌کند.
- **FR-047**: research MUST از operation/event موجود با lock order و publication guard مصوب استفاده کند. lease سی‌ثانیه‌ای فقط پیش از expiry توسط owner فعلی renew می‌شود و هر fetch حداکثر 20 ثانیه است؛ قبل و بعد I/O renew/recheck انجام می‌شود. network/انتظار pacing خارج transaction است و worker restart network work را خودکار تکرار نمی‌کند.
- **FR-048**: source allowlist MUST exact hostname، port، path prefix و redirect destination داشته باشد. اتصال واقعی فقط به IP public resolve‌شده و validate‌شده pin شود، درحالی‌که TLS SNI/certificate و Host برای hostname اصلی حفظ می‌شوند؛ proxy محیط، cookie، credential یا private user data در fetch مجاز نیست.
- **FR-049**: API پژوهش MUST request/response/error typed برای start/status/cancel ارائه کند؛ GET/replay/read research را آغاز نکند، submission یکسان active را deduplicate کند، progress فقط completed work باشد و partial success، no supported source، blocked policy، extraction failure، timeout، cancellation و stale ownership را جدا گزارش کند.
- **FR-050**: هر research target MUST یک source identifier و product URL صریح داشته باشد؛ domain تنها product selection نیست. fixture synthetic MAY URL نداشته باشد، اما `LIVE` target MUST به policy همان source و exact allowed destination/path وابسته باشد. replay همان payload اصلی را برگرداند و brief جدید را جایگزین expected revision درخواست قدیمی نکند.
- **FR-051**: acceptance MUST زیر lock order موجود، مالکیت/expiry conversation، confirmation، expected brief revision و generation، target-mode association، idempotency و guest admission را اتمیک بازبینی کند. boolean revision و list/object malformed MUST با 4xx تعریف‌شده رد شوند.
- **FR-052**: fetch/extraction candidate خارج lock ساخته شود، ولی snapshot، product/variant/offer/claims، counters و `evidence.published`/progress MUST به‌صورت یک per-source transaction پس از revalidation conversation/operation/job/policy ذخیره شوند. stale/cancel/delete/expiry/lease loss یا rollback MUST هیچ evidence unit یا orphan identity باقی نگذارد؛ cache reuse همین guard را دارد.
- **FR-053**: SafeFetcher MUST DNS resolution، pacing/capacity، connect/TLS/header/body و کل request/job را با remaining deadline محدود کند؛ compressed wire و decoded bytes، malformed/truncated/composite gzip و normalized path/redirect destination policy را enforce کند. test-only connector MAY controlled localhost server را استفاده کند، ولی production SSRF policy تغییر نکند.
- **FR-054**: persisted job limits MUST execution budget واقعی را بسازند و request/redirect/wire/decoded counters و coverage failure codeها را ثبت کنند. هر job فقط یک sequential lease owner دارد؛ process-local outbound semaphore global نیست. ResearchJob و StreamOperation در submission failure، cancel، exception، stale lease/brief/expiry و completion MUST در یک transition یا reconciliation authoritative همگرا شوند و network خودکار restart نشود.
- **FR-055**: Phase 9.2 MAY فقط sourceهای عمومی بدون منع صریح در material بررسی‌شده را برای pilot خواندنی، با exact product path، attribution، field minimization، raw retention حداکثر 24h، evidence owner-scoped، freshness حداکثر 6h و pace حداقل 2s فعال کند. `robots` allowance یا HTTP 200 مجوز عمومی نیست و terms/robots/extraction باید statusهای جدا بمانند.
- **FR-056**: LIVE extractor MUST برای هر offer، exact variant identity، merchant identity، product/source URL، merchant URL در صورت وجود، original numeric price/currency، normalized `price_toman`، availability، shipping/mandatory-charge unknown، warranty/condition، observation time، freshness و `COMPARISON_OBSERVED|MERCHANT_PAGE_VERIFIED` را جدا نگه دارد. Rial فقط با rule صریح `10 IRR = 1 TOMAN` normalize می‌شود؛ unit از magnitude حدس زده نمی‌شود.
- **FR-057**: offer comparison MUST فقط variantهای compatible را گروه کند، same merchant/offer را در sourceها deduplicate کند و discrepancy میان comparison observation و merchant verification را حفظ کند. Merchant SKU به‌تنهایی cross-store identifier نیست.
- **FR-058**: research API MUST offer view منبع‌دار و deterministic ارائه کند. sort اول lowest observed item price میان comparable offerهاست؛ lowest total payable فقط وقتی shipping و mandatory componentها معلوم‌اند. unknown total MUST جدا بماند.
- **FR-059**: copilot route MUST exact product URL list محدود، action صریح research، progress، partial/source failure و offer panel فارسی/RTL را نشان دهد. برچسب محدوده قیمت باید «کمترین قیمت بین منابع بررسی‌شده» باشد و MUST NOT پوشش بازار یا delivered-price کامل را ادعا کند. LIVE، cache، stale، captured fixture و synthetic جدا نشان داده شوند.
- **FR-060**: Phase 9.2 live pilot MUST حداکثر 100 outbound HTTP request شامل policy check، redirect و retry داشته باشد، actual usage را ثبت کند و public-source observation را از deterministic regression suite جدا نگه دارد. fixture fallback، provider call، account، purchase و bypass ممنوع است.

### Key Entities *(include if feature involves data)*

- **Conversation / Message**: مالکیت مهمان، lifecycle، turn و محتوای کاربر/assistant با state provisional/final.
- **ShoppingBrief**: snapshot نسخه‌دار نیاز، budget، context، constraint، preference و unknownهای تأییدشده.
- **ResearchJob / SourcePolicy / SourceSnapshot**: کار bounded، قواعد domain و evidence دریافت‌شده با provenance/freshness.
- **Product / Variant / Offer / EvidenceClaim**: هویت محصول، variation، مشاهدهٔ بازار و claim field-level.
- **ChoiceSet / RankingRun**: shortlist، criterionهای نسخه‌دار، hard filters، score components و explanation.
- **PreferenceMemory**: preference opt-in و provenance/confirmation/deletion state آن.
- **UserCredential / AIInvocation**: secret رمز‌شده و metadata/cost غیرحساس تماس؛ بدون raw key.
- **StreamOperation / StreamEvent**: state عملیات، cancellation و eventهای replay-safe.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: تمام scenarioهای سه category fixture یک brief با context/budget/unknown صریح و بدون fact ساختگی تولید می‌کنند.
- **SC-002**: برای dataset رتبه‌بندی ثابت، ۱۰۰٪ اجرای تکراری ترتیب، tie، hard-filter و total-cost یکسان می‌دهد و هر component به rule/evidence ردیابی می‌شود.
- **SC-003**: ۱۰۰٪ claimهای نمونهٔ Choice Desk attribution/citation و timestamp مناسب دارند؛ variant مبهم merge نمی‌شود.
- **SC-004**: cancellation/reconnect testها هیچ stale publication یا duplicate final message ایجاد نمی‌کنند و state نهایی از API قابل بازیابی است.
- **SC-005**: آزمون‌های privacy نشان می‌دهند memory خاموش چیزی persist نمی‌کند و raw API key در response، log، bundle، export یا repository ظاهر نمی‌شود.
- **SC-006**: journey اصلی در viewportهای mobile/desktop با keyboard قابل تکمیل است، serious/critical accessibility finding صفر دارد و stream قابل توقف است.
- **SC-007**: هر research job از limits مصوب عبور نمی‌کند و برای timeout/403/429/CAPTCHA/oversize وضعیت صریح ثبت می‌کند.
- **SC-008**: Compose rehearsal با fixture و بدون provider key بالا می‌آید؛ live mode برای credential/eligibility/budget ناقص پیش از call واضح fail closed می‌شود.

## Assumptions

- guest-first و same-browser continuity تا تصمیم تازه حفظ می‌شود؛ cross-device recovery تضمین نیست.
- سه category نماینده برای قرارداد و fixture عبارت‌اند از electronics، home appliance و sports/fashion؛ این انتخاب coverage بازار را ثابت نمی‌کند.
- در milestone اولیه sourceهای manufacturer و merchant با policy صریح بر aggregator/reviewهای نامطمئن اولویت دارند.
- SSE برای downstream server-to-browser کافی فرض شده و فقط با evidence implementation تغییر می‌کند.
- eligibility مستقیم OpenAI برای users/backend ایران تأیید نشده است؛ GapGPT selected path نیز تا credential محلی، validation واقعی و مجوز هزینه live-verified نیست.
- retention مصوب Milestone A برای conversation/message/current brief برابر 90 روز پس از eligible action و برای upload/event برابر 24 ساعت است؛ در Milestone B raw research حداکثر 24 ساعت و evidence خصوصی حداکثر تا expiry conversation است. retention memory/credential فقط در milestone مربوط تصمیم‌گیری می‌شود.

## Settings correction authorization (2026-11-16)

- **FR-088**: Provider transitions MUST invalidate previous credential state before loading the new provider; failed loading MUST expose retry and MUST NOT permit saving/deleting a different provider's credential. Settings remain recoverable after revision conflicts. Restore the existing local encryption mount without rotating keys or changing data.
  Mutations MUST be serialized before React re-render, and obsolete async continuations MUST be ignored after leaving/reloading settings. Test rapid selection, duplicate save/delete and failed provider loading. Offline startup without the optional secret remains supported.
- **FR-089**: Research free API onboarding using primary sources, distinguishing quotas from eligibility and measured quality. Do not activate an unverified Iran route, automatic paid fallback or provider calls. A new usable integration requires an eligible fixed model/protocol/privacy contract; unresolved requirements remain explicitly pending.

## Out of Scope

- checkout، خرید خودکار، affiliate optimization، price alert و افزایش budget.
- bypass کردن CAPTCHA/login/paywall/robots/anti-bot یا crawling انبوه.
- provision کردن GPU/model بزرگ روی Mac، provider-routing framework یا fallback پنهان. self-hosting فقط با feasibility و infrastructure authorization جدا مجاز است.
- account اجباری، social/public conversation sharing و cross-device recovery در این feature.
- تشخیص روان‌شناختی، پیش‌بینی علمی regret و استخراج ویژگی حساس.
- ranking/Choice Desk کامل، personalized alternatives، memory، credential، live AI و public deployment در Phase 9.2 مجاز نیستند؛ offer panel حداقلی صراحتاً مجاز است.
