# تحویل Phase 5.2 — انتخاب provider مناسب ایران

**تاریخ:** ۱۴ نوامبر ۲۰۲۶  
**وضعیت:** adaptation مستقل کامل؛ live evaluation و review انسانی pending  
**مرز:** فقط M3؛ بدون خرید/شارژ/ثبت‌نام، deployment، M4، commit یا push

## 1. نتیجه و Spec Kit

- context قطعی ایران و cap کل evaluation برابر ۱۰۰٬۰۰۰ تومان در feature موجود ثبت شد.
- requirementهای `FR-041..FR-044`، acceptanceهای `AC-AI-008..010` و taskهای `T049..T052` اضافه شدند.
- `$speckit-analyze` با prerequisite رسمی و checklistهای 30/30 و 25/25 اجرا شد. دو ناسازگاری تاریخی region/budget
  اصلاح شدند؛ conflict بحرانی یا constitution violation باقی نماند.
- `T049..T052` تکمیل شدند. `T039` عمداً باز است تا هم live evidence واقعی و هم review انسانی کامل وجود داشته باشد.
  `T041..T043` مربوط به M4 دست‌نخورده‌اند.

## 2. providerهای مقایسه‌شده

| provider | evidence رسمی | نتیجه |
|---|---|---|
| AvalAI | [Quick Start](https://docs.avalai.ir/en/quickstart)، [Models API](https://docs.avalai.ir/en/api-reference/models)، [User API](https://docs.avalai.ir/en/api-reference/user)، [Privacy](https://avalai.ir/privacy-policy/)، [سایت](https://avalai.ir/) | انتخاب محدود برای integration/evaluation: Responses مستند، schema، model/tariff، usage/request ID و cost API |
| Liara AI | [تعرفه](https://liara.ir/pricing/)، [مدل بررسی‌شده](https://liara.ir/products/ai/xAI%3A%20Grok%203%20Mini%20Beta/) | رد برای این فاز: `x-ai/grok-3-mini-beta` Structured Outputs غیرفعال و پلن پایه AI ماهانه ۲۹۹هزار تومان است |

ادعای performance هیچ‌کدام در این workspace اندازه‌گیری نشد. listing مدل، authorization upstream یا data-handling
upstream را ثابت نمی‌کند.

## 3. انتخاب و عدم‌قطعیت‌ها

- انتخاب: AvalAI Responses API روی `https://api.avalai.ir/v1` با model ID دقیق `gpt-5.6-luna`.
- مستند AvalAI هم Responses و هم Chat Completions را نشان می‌دهد؛ این implementation عمداً Responses را اجرا می‌کند.
  انتخاب بر پایه «OpenAI-compatible» بودن نیست.
- مدل در Models API دارای `supports_response_schema=true` است. adapter schema strict، `store=false`، timeout ۸ ثانیه،
  حداکثر دو attempt transient، usage و `avalai-request-id` را مصرف می‌کند.
- کیفیت فارسی، semantic support، latency و usefulness هنوز اندازه‌گیری نشده‌اند.
- unresolved و blocker activation: پاسخ مکتوب AvalAI دربارهٔ authorization/route upstream برای ایران، محل و مدت
  نگهداری prompt/output در AvalAI و upstream، مجازبودن کاربرد محصول، و امکان مصرف signup grant برای همین مدل بدون
  top-up/minimum balance. سؤال‌های دقیق در `docs/backend-operations.md` ثبت شده‌اند؛ هیچ پیام خارجی ارسال نشد.
- direct OpenAI در factory غیرفعال است. حتی تنظیم legacy region flag یا وجود `OPENAI_API_KEY` آن را انتخاب نمی‌کند.

## 4. تعرفه و budget

- تعرفهٔ Models API در تاریخ این تحویل: input برابر `$5/M`، cached input برابر `$0.5/M` و output برابر `$30/M`.
  reservation برای محافظه‌کاری cached discount را فرض نمی‌کند.
- AvalAI مبلغ را به UNIT/USD قیمت‌گذاری و `exchange_rate` و هزینهٔ IRT را گزارش می‌کند؛ IRT در قرارداد آن تومان است.
  نرخ واقعی این workspace خوانده نشد چون credential محلی وجود ندارد. پیش از call، command نرخ تازه را از `/credit`
  می‌گیرد و margin ارزی ۱۵٪ اعمال می‌کند.
- فرمول: `estimated_toman = microUSD / 1,000,000 × IRT_per_UNIT × 1.15`.
- اگر منبع حسابداری ریال باشد، conversion صریح `10 rial = 1 toman` است.
- cap کل هفت case با همه retryها حداکثر ۱۰۰٬۰۰۰ تومان است. cap محلی estimate محافظه‌کارانه است، نه تضمین invoice.
- `price_toman` و `budget_toman` خرید هیچ‌جا برای accounting AI استفاده نمی‌شوند؛ ledger AI در microUSD و metadata
  provider در تومان جدا نگه داشته می‌شوند.

## 5. تغییرات implementation

- `analysis.ai.avalai_adapter`: transport مستند Responses، طبقه‌بندی خطا، usage/request-id/cost metadata، User Credit API.
- `analysis.ai.avalai_pricing`: تعرفهٔ مدل منتخب، تبدیل تومان با margin و cap محافظه‌کارانه.
- factory/settings: فقط provider=`avalai` با eligibility/key/rate/budget صریح؛ direct OpenAI fail closed.
- `AIInvocation`: migration `0003` برای `provider_request_id` و `provider_estimated_cost_toman`؛ هیچ raw prompt/response
  یا secret ذخیره نمی‌شود.
- evaluation command: cap صریح تومان، سقف hard برابر ۱۰۰٬۰۰۰، credit/rate preflight، reservation هفت case و retryها،
  artifact baseline-versus-AI با human fields برابر null.
- `.env.example`، operations، research، data model، quickstart، tooling inventory و قراردادهای Spec Kit به‌روز شدند.

## 6. verification

| بررسی | نتیجه |
|---|---|
| red phase | نبود adapter/gateهای AvalAI: ۲ failure و ۲ error معنادار |
| AvalAI + evaluation focused | ۹ تست پاس |
| AI suite نهایی | ۳۱ تست پاس |
| affected AI/validator/concurrency | ۴۴ تست پاس |
| backend کامل روی PostgreSQL | ۹۶ تست پاس |
| Django system check | issue صفر |
| migration drift | `No changes detected` |
| Python compile/AST | پاس |
| diff whitespace | پاس |

container قدیمی dev dependency قفل‌شدهٔ PyYAML را نداشت؛ suite کامل با محیط `uv.lock` محلی و PostgreSQL Compose
اجرا شد. این خطای image به M4/deployment گسترش داده نشد.

## 7. live evidence و مراحل pending

- `AVALAI_API_KEY`: در محیط محلی **موجود نبود**.
- eligibility clarification: **تکمیل نشده**.
- model call: **۰**؛ retry: **۰**؛ token: **۰**؛ هزینهٔ واقعی/estimate provider: **۰ تومان**.
- artifact live/human: ساخته نشد؛ output mock یا stub به‌عنوان evidence زنده گزارش نشد.

پس از دریافت clarification و فقط با حساب/credit ازقبل‌موجود، بدون ارسال key در chat:

```bash
export AVALAI_API_KEY='<local-secret>'
curl -sS https://api.avalai.ir/user/v1/credit \
  -H "Authorization: Bearer $AVALAI_API_KEY"

export BEFOREBUY_AI_MODE=live
export BEFOREBUY_AI_PROVIDER=avalai
export BEFOREBUY_AVALAI_ELIGIBILITY_CONFIRMED=1
export BEFOREBUY_AI_MODEL=gpt-5.6-luna
export BEFOREBUY_LIVE_EVAL_BUDGET_TOMAN=100000
python backend/manage.py evaluate_live_ai --artifact-dir artifacts/ai-evaluation
python backend/manage.py assess_ai_review artifacts/ai-evaluation/<run-id>.json
```

اگر `/credit` موجودی/scope کافی نشان نداد، متوقف شوید؛ subscription، top-up یا ثبت‌نام در اختیار این فاز نیست.
Reviewer باید چهار field `semantic_support`, `readability`, `actionability`, `added_usefulness` را برای هر هفت case
پر کند. تا آن زمان `overall_pass=null` و `T039` باز می‌ماند.

**Phase 5.2 adaptation complete; live evidence and human review pending.**
