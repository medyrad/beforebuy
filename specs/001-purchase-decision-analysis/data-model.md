# Data Model

**Feature**: `001-purchase-decision-analysis`  
**Lifecycle invariant**: فقط latest required state نگهداری می‌شود؛ `expires_at = created_at + 90 days` و هرگز
نمی‌لغزد.

## Entity map

```text
DjangoSession ── stores guest_context_id ──> GuestContext
GuestContext 1 ─────────────────────────── * Analysis
Analysis     1 ─────────────────────────── 1 CurrentReport
Analysis     1 ────────────────────────── 0..1 UsefulnessFeedback
GuestContext 1 ─────────────────────────── * AIInvocation
AILiveBudgetWindow 1 ───────── reserves/settles ───── * AIInvocation
```

`Evidence` table جدا ندارد: evidence فقط همراه current report خوانده/جایگزین می‌شود و requirement جست‌وجوی مستقل
ندارد، پس به‌صورت typed JSON در `CurrentReport` ذخیره می‌شود. answerها نیز schema-versioned JSON هستند. این تصمیم
از table-per-question جلوگیری می‌کند، در حالی که ownership، expiry و feedback با constraint رابطه‌ای می‌مانند.

## GuestContext

| Field | Type / constraint | Purpose |
|---|---|---|
| `id` | UUID PK, random | opaque guest owner؛ در session server-side نگهداری می‌شود |
| `created_at` | timestamptz immutable | lifecycle anchor guest context |
| `access_expires_at` | timestamptz | bootstrap + 90d؛ فقط persist analysis جدید تا expiry همان analysis تمدیدش می‌کند |
| `generation_epoch` | bigint, default 0, nonnegative | clear-history barrier برای initial createهای بدون Analysis row |

هیچ email، account، device fingerprint یا recovery token ذخیره نمی‌شود. گم‌شدن cookie یعنی عدم امکان recovery.

## Analysis

| Field | Type / constraint | Purpose |
|---|---|---|
| `id` | UUID PK | public opaque identifier |
| `guest_context_id` | FK, indexed, cascade | ownership boundary |
| `input_revision` | positive integer, starts 1 | optimistic concurrency و stale-result rejection |
| `rubric_id` | varchar, currently `PDA-CAT-v0.3` | reproducibility |
| `questionnaire_schema` | varchar | decoding answers |
| `product_label` | varchar(120) | `PC-001` |
| `price_toman` | bigint, `> 0` | normalized whole toman |
| `budget_toman` | bigint nullable, `>= 0` | null فقط به معنی explicit unknown |
| `answers` | JSONB object | Q/F values با allowlist schema؛ نه raw prompt |
| `created_at` | timestamptz immutable | اولین persisted success/limited report |
| `expires_at` | timestamptz immutable, indexed | `created_at + 90d` |
| `report_operation_token` | UUID nullable | آخرین edit/retry مجاز به publish برای input revision جاری |
| `updated_at` | timestamptz | latest state write؛ retention را تغییر نمی‌دهد |

Validation: هر analysis باید یک `CurrentReport` داشته باشد؛ creation هر دو atomic است. application query همیشه
`guest_context_id = session owner AND expires_at > now()` را اعمال می‌کند. delete hard-delete و cascade است.

## CurrentReport

| Field | Type / constraint | Purpose |
|---|---|---|
| `analysis_id` | one-to-one PK/FK, cascade | فقط report جاری |
| `report_revision_id` | UUID unique | rating/content ownership |
| `input_revision` | integer | باید با Analysis هنگام publish برابر باشد |
| `rubric_id` | varchar | frozen engine version |
| `mode` | enum | `AI_ASSISTED_SUCCESS`, `MOCK_ASSISTED` یا `RULE_BASED_LIMITED` |
| `primary_outcome` | outcome enum | دقیقاً یک مقدار `OUT-*` |
| `dimensions` | JSONB typed object | exactly-one budget/justification/target/tradeoff |
| `matched_rule_ids` | JSONB string array | explanation traceability |
| `evidence` | JSONB typed array | `{id,type,source_id,value,attribution}`؛ allowlisted؛ attribution یکی از چهار مقدار `FR-010` |
| `unknowns` | JSONB typed array | scoped unknownها |
| `actions` | JSONB typed array | including repair/wait noted suggestions |
| `headline_fa` | text | validated visible prose |
| `explanation_blocks` | JSONB typed array | هر block evidence/rule references دارد |
| `canonical_hash` | fixed string | hash canonical visible payload + mode |
| `created_at` | timestamptz | report revision creation |

اگر retry hash و mode یکسان بدهد row/report revision تغییر نمی‌کند. هر تغییر visible یا mode یک UUID جدید می‌سازد و
feedback در همان transaction حذف می‌شود. هیچ report revision قدیمی persist نمی‌ماند.

## AIInvocation

این جدول فقط metadata عملیاتی live adapter را نگه می‌دارد و هیچ prompt، response، answer، evidence یا label خام در آن
persist نمی‌شود.

| Field | Type / constraint | Purpose |
|---|---|---|
| `id` | UUID primary key | شناسهٔ داخلی invocation |
| `guest_context_id` | FK cascade | اجرای limit روزانه بدون session identifier در log |
| `operation_id` | UUID unique | idempotent reservation برای یک generation operation |
| `provider` / `model` | bounded varchar | breakdown نسخهٔ provider/model |
| `prompt_version` / `schema_version` | bounded varchar | reproducibility بدون raw payload |
| `status` | reserved/succeeded/failed/rejected | lifecycle محدود invocation |
| `error_class` | bounded nullable enum-like string | طبقه‌بندی امن؛ نه متن exception |
| `attempt_count` | non-negative small integer | اثبات سقف attempt |
| `input_tokens` / `output_tokens` | nullable non-negative integers | usage اعلام‌شده provider در صورت وجود |
| `latency_ms` | nullable non-negative integer | latency کل adapter |
| `reserved_cost_microusd` | non-negative bigint | worst-case reservation پیش از call |
| `estimated_cost_microusd` | non-negative bigint | settlement محافظه‌کارانه |
| `provider_request_id` | nullable bounded string | AvalAI request ID برای ردیابی هزینه؛ payload نیست |
| `provider_estimated_cost_toman` | nullable decimal | estimate گزارش‌شده provider؛ invoice قطعی نیست |
| `created_at` / `completed_at` | timestamptz | window و audit عملیاتی |

## AILiveBudgetWindow

| Field | Type / constraint | Purpose |
|---|---|---|
| `day` | date primary key (UTC) | deployment-wide daily window |
| `reserved_cost_microusd` | non-negative bigint | بودجهٔ callهای درحال اجرا |
| `spent_estimate_microusd` | non-negative bigint | هزینهٔ settle‌شده همان روز |
| `consecutive_failures` | non-negative integer | وضعیت circuit مشترک بین processها |
| `circuit_open_until` | timestamptz nullable | rejection سریع تا پایان cooldown |
| `updated_at` | timestamptz | audit تغییر وضعیت |

reservation با `select_for_update` روی window روز انجام می‌شود، سقف per-guest را از `AIInvocation`های همان روز
می‌شمارد و worst-case cost تمام attemptهای مجاز را رزرو می‌کند. provider call خارج transaction است. settlement در
transaction کوتاه reservation را آزاد و usage اعلام‌شده را charge می‌کند؛ اگر usage قابل اعتماد موجود نباشد کل
reservation charge می‌شود. settlement تکراری no-op است، usage واقعی تا reservation clip نمی‌شود و overage در اختلاف
دو field و spent total باقی می‌ماند. success failure count را صفر می‌کند و failure گذرا/provider آن را افزایش می‌دهد؛ رسیدن
به threshold، circuit مشترک را تا cooldown باز می‌کند. rejected invocation provider call ندارد.

نام fieldهای `*_microusd` واحد تعرفهٔ مدل AI را نگه می‌دارند و با پول خرید (`price_toman`/`budget_toman`) مخلوط
نمی‌شوند. برای AvalAI، preflight با نرخ تازهٔ `IRT-per-UNIT` و margin ۱۵٪ cap تومان را به سقف محافظه‌کارانهٔ
micro-USD تبدیل می‌کند. `provider_estimated_cost_toman` فقط evidence provider است؛ transaction lookup/invoice مرجع نهایی است.

## UsefulnessFeedback

| Field | Type / constraint | Purpose |
|---|---|---|
| `analysis_id` | one-to-one PK/FK, cascade | حداکثر یک rating جاری |
| `report_revision_id` | UUID | باید با CurrentReport جاری برابر باشد |
| `report_mode` | enum | metric breakdown بدون join تاریخی |
| `rating` | smallint, check `1..5` | پاسخ اختیاری |
| `updated_at` | timestamptz | change timestamp، نه retention anchor |

write feedback با expected `report_revision_id` انجام می‌شود؛ mismatch برابر `409`. metric فقط average/count روی
feedbackهای retained و breakdown بر اساس mode است.

## State transitions

```text
browser draft --valid report generated--> ACTIVE revision 1
ACTIVE --edit + publish--> ACTIVE input revision n+1 / new current report
ACTIVE --retry identical--> ACTIVE unchanged
ACTIVE --retry visible change--> ACTIVE new report revision / no rating
ACTIVE --expires_at reached--> UNAVAILABLE --daily purge--> REMOVED
ACTIVE --delete--> REMOVED
```

- generation failure بدون displayable limited report: هیچ Analysis ساخته نمی‌شود.
- edit ابتدا input revision را conditional increment می‌کند و report قبلی را stale می‌سازد؛ فقط publish current revision
  می‌تواند CurrentReport را replace کند.
- late response برای revision قدیمی، rubric دیگر، owner دیگر، expired یا missing row: discard، بدون insert/resurrection.
- initial create، epoch مهمان را پیش از work طولانی capture می‌کند. publish و clear-history هر دو همان GuestContext را
  در transaction کوتاه lock می‌کنند؛ clear epoch را increment و data را حذف می‌کند، publish فقط epoch برابر insert دارد.
- هر edit/retry یک operation token جدید می‌سازد؛ publish token قدیمی حتی روی همان input revision برابر conflict/discard است.
- lock/transaction در provider/network call نگه داشته نمی‌شود.

## Indexes and constraints

- `Analysis(guest_context_id, expires_at, created_at DESC)` برای history.
- `Analysis(expires_at)` برای purge batch.
- `GuestContext(access_expires_at)` برای cleanup contextهای بدون analysis.
- unique `CurrentReport.report_revision_id`.
- unique `AIInvocation.operation_id` و index روی `(guest_context_id, created_at)` برای limit روزانه.
- checkهای non-negative برای counter/token/costهای AI و `attempt_count <= 2`.
- checkهای money، rating و positive revision در DB علاوه بر serializer/domain validation.
- JSON schema در application boundary validate می‌شود؛ migration تغییر schema باید backward-readable یا data migration
  صریح داشته باشد.

## Retention and deletion

- active access در query layer فوراً در expiry بسته است، حتی اگر physical purge عقب باشد.
- purge حداقل روزانه اجرا می‌شود و target حذف active records حداکثر ۲۴ ساعت است.
- persist analysis جدید `GuestContext.access_expires_at` و Django session/cookie expiry را تا expiry آن analysis
  تمدید می‌کند؛ read/edit/retry/feedback این کار را نمی‌کنند. پاک‌شدن یا expiry زودتر cookie توسط browser می‌تواند
  دسترسی را پیش از آن قطع کند و recovery بین browser/device وجود ندارد.
- cleanup روزانه contextهای expired بدون analysis و `clearsessions` استاندارد Django را نیز اجرا می‌کند.
- backup retention/restore و deletion caveat پیش از production تعیین می‌شود؛ API نباید حذف فوری از backup را وعده دهد.
- logs و جدول‌های AI، answer/evidence/session/raw prompt/raw response یا exception text را نگه نمی‌دارند.
