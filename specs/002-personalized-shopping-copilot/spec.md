# Feature Specification: دستیار شخصی خرید

**Feature Branch**: `002-personalized-shopping-copilot`

**Created**: 2026-11-15

**Status**: Planned; implementation not started

**Input**: تبدیل Beforebuy از پرسش‌نامهٔ تلفن به دستیار گفت‌وگومحور چنددسته‌ای با پژوهش محدود، میز انتخاب، حافظهٔ opt-in و کلید OpenAI متعلق به کاربر.

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

---

### User Story 5 - حافظه و کلید تحت کنترل کاربر (Priority: P2)

کاربر می‌تواند preferenceهای مشخص را opt-in ذخیره، مشاهده، اصلاح یا حذف کند و کلید OpenAI خود را به‌صورت masked مدیریت کند. temporary conversation و candidate inference خودکار حافظهٔ دائمی نیستند.

**Why this priority**: شخصی‌سازی و هزینهٔ user-owned بدون consent، deletion و secret safety قابل قبول نیست.

**Independent Test**: consent، isolation، encrypt/decrypt boundary، masking، deletion، rotation و region gate با credential synthetic بررسی می‌شوند و هیچ تماس live لازم نیست.

**Acceptance Scenarios**:

1. **Given** memory خاموش است، **When** preference در گفت‌وگو بیان می‌شود، **Then** خارج از retention گفت‌وگو به profile منتقل نمی‌شود.
2. **Given** یک inferred candidate وجود دارد، **When** کاربر آن را تأیید نکرده، **Then** recommendation آینده آن را preference قطعی تلقی نمی‌کند.
3. **Given** key ذخیره شده، **When** UI یا log نمایش می‌دهد، **Then** plaintext هرگز برنمی‌گردد و replace/delete ممکن است.
4. **Given** کاربر/backend در ایران است، **When** فقط key وارد شده، **Then** live activation همچنان blocked می‌ماند تا region eligibility مستقل تأیید شود.

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
- **FR-018**: هر claim قابل مشاهده MUST citation یا attribution `USER_REPORTED`, `DETERMINISTIC`, `VERIFIED_SOURCE`, `ASSISTANT_INFERENCE`, یا `UNKNOWN` داشته باشد.
- **FR-019**: recommendation MUST توضیح دهد چرا، با کدام tradeoff، تحت چه uncertainty و چه evidence تازه‌ای تغییر می‌کند؛ هدف افزایش خرید یا budget نیست.
- **FR-020**: stream MUST event ID، operation ID، sequence، type، timestamp و payload version داشته باشد؛ provisional delta fact نهایی محسوب نمی‌شود.
- **FR-021**: stream MUST progress واقعی مرحله/تعداد bounded work را ارسال کند و MUST hidden chain-of-thought، progress جعلی یا secret منتشر نکند.
- **FR-022**: cancellation MUST cooperative باشد و publication با operation token/revision guard جلوی late/stale result را بگیرد؛ state نهایی از API authoritative است.
- **FR-023**: preference memory MUST default-off و opt-in باشد؛ explicit preference، inferred candidate و context موقت جدا و review/correct/delete/disable داشته باشند.
- **FR-024**: conversation، message، upload، research snapshot، memory، credential و cost record MUST purpose، retention، deletion و owner جدا داشته باشند؛ حذف فوری backup فقط در صورت policy اثبات‌شده ادعا شود.
- **FR-025**: user-owned OpenAI key MUST فقط backend-side، encrypted at rest، masked، replaceable/deletable و از log/frontend/URL/Git/merchant request دور بماند؛ encryption key جدا از database نگه‌داری شود.
- **FR-026**: runtime AI feature جدید MUST direct OpenAI Responses API only باشد و هیچ fallback پنهان به AvalAI/provider دیگر نداشته باشد.
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
- **SC-008**: Compose rehearsal با fixture و بدون OpenAI key بالا می‌آید؛ live mode برای region/config ناقص پیش از call واضح fail closed می‌شود.

## Assumptions

- guest-first و same-browser continuity تا تصمیم تازه حفظ می‌شود؛ cross-device recovery تضمین نیست.
- سه category نماینده برای قرارداد و fixture عبارت‌اند از electronics، home appliance و sports/fashion؛ این انتخاب coverage بازار را ثابت نمی‌کند.
- در milestone اولیه sourceهای manufacturer و merchant با policy صریح بر aggregator/reviewهای نامطمئن اولویت دارند.
- SSE برای downstream server-to-browser کافی فرض شده و فقط با evidence implementation تغییر می‌کند.
- eligibility مستقیم OpenAI برای users/backend ایران در تاریخ planning تأیید نشده و release blocker است.
- retention دقیق conversation/upload/research cache/credential پیش از implementation در task مربوط با privacy review نهایی می‌شود؛ default پیشنهادی کمینه و قابل پیکربندی است.

## Out of Scope

- checkout، خرید خودکار، affiliate optimization، price alert و افزایش budget.
- bypass کردن CAPTCHA/login/paywall/robots/anti-bot یا crawling انبوه.
- self-hosted model/GPU، provider abstraction چندگانه یا fallback به AvalAI.
- account اجباری، social/public conversation sharing و cross-device recovery در این feature.
- تشخیص روان‌شناختی، پیش‌بینی علمی regret و استخراج ویژگی حساس.
- implementation در Phase 7؛ این سند فقط specification و planning را مجاز می‌کند.
