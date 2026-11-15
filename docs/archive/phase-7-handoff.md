# تحویل Phase 7 — Shopping Copilot specification and planning

**تاریخ:** ۱۵ نوامبر ۲۰۲۶  
**baseline:** `805837108bbb3a48ad2e66163ddce90fc6b24f32`  
**branch:** `002-personalized-shopping-copilot`  
**وضعیت:** specification/planning کامل؛ implementation شروع نشده  
**مرز:** بدون migration، dependency اپ، provider call، crawl انبوه، deployment یا تغییر runtime

## نتیجه

feature canonical تازه در `specs/002-personalized-shopping-copilot/` ساخته شد. Beforebuy برای جهت جدید به‌صورت
shopping copilot فارسی/RTL، conversation-first، چنددسته‌ای، evidence-grounded و دارای Choice Desk تعریف شده است.
feature 001 و شواهد آن حفظ شده‌اند؛ `T039` آن همچنان unchecked است و هیچ cutover رخ نداده است.

## گردش‌کار Spec Kit

1. constitution با approval product lead از `1.0.0` به `2.0.0` amend شد؛ phone-only/broad-research ban با governance
   چنددسته‌ای، bounded retrieval، streaming، memory و user-owned secret جایگزین شد.
2. `speckit-specify` feature 002، acceptance scenarioها، 36 requirement و هشت success criterion را ساخت.
3. clarification scan marker بحرانی پیدا نکرد؛ region، source permission و retention به‌عنوان gate صریح باقی ماندند.
4. `speckit-plan` artifacts فنی، data model، OpenAPI، stream contract، research، design، ranking و migration را ساخت.
5. `speckit-tasks` تعداد 50 task باز را در milestoneهای A–E تولید کرد؛ هیچ task تیک نخورده است.
6. تحلیل نخست دو gap با severity High برای upload backend و export مالک پیدا کرد. `T049/T050` و endpoint/model مرتبط
   اضافه شدند. تحلیل دوم 36 requirement و 8 success criterion ساختنی را به 50 task map کرد: coverage برابر 100٪،
   task بدون هدف صفر، placeholder صفر، تعارض constitution صفر و Critical/High صفر.

## جهت محصول و design

- journey: conversation → confirmed brief → explicit bounded research → Choice Desk → optional memory.
- Choice Desk Concept 2 یک فضای editorial/analytical است: conversation rail، brief ribbon، desk canvas و research
  ledger. Mobile به horizontal scroll ضروری وابسته نیست.
- ranking `COPILOT-RANK-v0.1` ابتدا hard filter و total payable cost قطعی را اجرا می‌کند؛ missing evidence unknown است،
  tie deterministic است و LLM fact/price/arithmetic/rank authoritative نمی‌سازد.
- stream contract با REST + SSE، event ID/sequence/version، provisional/final boundary، replay و cancellation طراحی شد.

## مهارت design

دو candidate رسمی Anthropic در commit `1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064` بررسی شدند:

- `frontend-design`: انتخاب و در `.agents/skills/frontend-design/` نصب شد؛ Apache-2.0، docs-only و بدون dependency runtime.
- `web-artifacts-builder`: به‌علت stack موازی React 18/Parcel/Tailwind/shadcn رد شد.

snapshotهای Vercel inactive ماندند. frontmatter/license/checksum نصب validate شد. چون catalog این turn پیش از install
ساخته شده بود، native catalog discovery نام skill در session بعد باید تأیید شود؛ invocation موفق فعلی ادعا نمی‌شود.
overlay پروژه در `choice-desk-design.md` Persian/RTL، accessibility، reduced motion، evidence semantics و React+Vite
موجود را مقدم می‌کند.

## امکان‌سنجی منابع

probeها کوچک، read-only و محدود به یک robots/page نماینده بودند:

| Domain | Evidence observed | نتیجه |
|---|---|---|
| Digikala | robots/root timeout در budget کوتاه | unassessed؛ disabled |
| Torob | robots timeout | unassessed؛ disabled |
| Technolife | robots 200 با content signals؛ redirect root سپس timeout | policy-only؛ extraction unresolved |
| Apple | robots 200؛ specs page 200/234,076 bytes و fields قابل مشاهده | electronics manufacturer fixture candidate |
| Philips | robots 200؛ product page 200/193,393 bytes و fields قابل مشاهده | appliance fixture candidate |
| Nike | robots `/p/` disallow؛ sample 404 بزرگ | initial fixture rejected |
| Decathlon/Adidas | official indexed docs surfaced؛ direct extraction ثبت نشد | documentation candidate only |

robots مجوز حقوقی جامع نیست و search snippet extraction نیست. electronics/appliance فقط manufacturer feasibility
دارند؛ Iranian offers و sports/fashion هنوز data-ready نیستند. CAPTCHA/login/paywall/anti-bot bypass ممنوع است.

## OpenAI و هزینه

feature 002 direct OpenAI Responses only و user-owned API key است؛ AvalAI feature 001 fallback نیست. exact model ID
پیش از implementation باید برای image/text، structured output، streaming، context و price revalidate شود. منابع رسمی
Responses، streaming، vision، data retention، key safety، pricing و supported countries ثبت شدند.

ایران در فهرست supported countries فعلی نیست. key، ChatGPT subscription یا credit eligibility را ثابت نمی‌کند؛
live activation با users/backend ایران fail closed است. calls این phase `0` و cost `0` است. ChatGPT subscription و
API billing جدا هستند. `store=false` به‌تنهایی ZDR/عدم abuse retention را تضمین نمی‌کند.

## معماری و privacy

- stack/topology موجود reuse می‌شود: React/Vite، Django/DRF، PostgreSQL، NGINX/Compose و same-origin.
- new entities: Conversation/Message/Brief، ResearchJob/SourcePolicy/Snapshot/Claim، Product/Variant/Offer،
  ChoiceSet/Item، PreferenceMemory، UserCredential و StreamOperation/Event.
- memory default-off است؛ candidate inference از confirmed preference و self/gift/household جداست.
- credential فقط ciphertext/envelope metadata در DB دارد؛ master key خارج DB/image/Git و library selection تا
  milestone D deferred است. custom cryptography ممنوع است.
- 90 روز conversation فقط proposal است؛ retention entityهای جدید پیش از implementation نیاز به approval دارد.

## همزیستی و milestoneها

- A: conversation/brief/fixture stream.
- B: source policy/fetch/extract/evidence برای categoryهای ready.
- C: deterministic Choice Desk و browser accessibility.
- D: opt-in memory، encrypted user key و stubbed OpenAI readiness.
- E: production rehearsal و gateهای جدا برای source/live/public.

Feature 001 تا تصمیم صریح cutover default باقی می‌ماند. analysis قدیمی خودکار migrate نمی‌شود، AvalAI config منتقل
نمی‌شود و rollback route/flag-based است. legacy retirement تصمیم جداست.

## فایل‌های اصلی

- `.specify/memory/constitution.md`
- `specs/002-personalized-shopping-copilot/{spec,plan,research,source-feasibility,choice-desk-design,ranking-evidence-rules,migration-coexistence,data-model,quickstart,tasks}.md`
- `specs/002-personalized-shopping-copilot/contracts/{openapi.yaml,stream-events.md}`
- `.agents/skills/frontend-design/` و اصلاح محدود `.agents/skills/purchase-regret-project/SKILL.md`
- `docs/{product-brief,decisions,tooling,handoff}.md`
- archive قبلی: `docs/archive/phase-6.2-handoff.md`

## Gateهای باز

1. source terms/permission و direct extraction برای Iranian offers و sports/fashion.
2. exact retention/export/backup erasure policy.
3. encryption dependency و master-key rotation/recovery operations.
4. official OpenAI region eligibility برای users/backend ایران، exact model capability و spending authorization.
5. implementation milestone authorization، target-host/public release و cutover decision.
6. feature 001 `T039`: live AvalAI evidence + human semantic review، همچنان pending.

## Working-tree preservation

حذف نامرتبط `test.txt` از ابتدا موجود بود و stage/commit نخواهد شد. secret، credential، dump، database، cache یا
runtime artifact ایجاد/اضافه نشده است.

## Verification اجراشده

- Spec Kit prerequisites با `--require-spec --require-tasks --include-tasks` feature 002 و همه artifacts را یافت.
- OpenAPI 3.1 با parser استاندارد Ruby parse شد و 13 path دارد.
- هر دو skill با validator قفل‌شدهٔ محیط پروژه `Skill is valid!` شدند.
- شمارش artifact: 36 FR، 8 SC، 50 task یکتا و همگی unchecked؛ placeholder اجرایی و task ID تکراری صفر.
- `git diff --check` بدون خطا اجرا شد. suite اپلیکیشن اجرا نشد، چون هیچ runtime behavior تغییر نکرد و Phase 7
  implementation را مجاز نمی‌کرد.

**Shopping Copilot specified and planned — implementation not started.**
