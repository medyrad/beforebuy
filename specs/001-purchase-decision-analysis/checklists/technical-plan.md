# Technical Plan Quality Checklist

**Purpose**: بررسی plan در برابر spec، constitution، rubric، lifecycle و AI boundary  
**Created / reviewed**: 2026-11-14  
**Artifacts**: [plan.md](../plan.md), [data-model.md](../data-model.md), [contract](../contracts/openapi.yaml)

## Architecture and constitution

- [x] monorepo modular monolith، single-server و Compose topology صریح است
- [x] Redis/Celery/microservice/SSR/JWT و layerهای بی‌نیاز وارد نشده‌اند
- [x] same-origin static frontend + API proxy و production/static boundary مشخص است
- [x] همه هشت اصل constitution پیش و پس از design بررسی و PASS شده‌اند
- [x] performance goalها target برنامه‌اند و measurement workspace جا زده نشده‌اند

## Rubric and API

- [x] `PDA-CAT-v0.3` تنها rule source است و engine از AI/ORM جداست
- [x] exact-one dimension و ordered exact-one primary outcome در test strategy آمده است
- [x] repair/wait فقط action flag است و target fit مستقل می‌ماند
- [x] API create/read/list/edit/reanalyze/delete/clear/feedback و error semantics را پوشش می‌دهد
- [x] request/response example و optimistic revision conflict در OpenAPI وجود دارد

## Data, ownership and lifecycle

- [x] Django server-side guest session، CSRF، owner filtering و non-enumerating 404 مشخص‌اند
- [x] first persisted report، 90-day non-sliding expiry و <=24h purge target مدل شده‌اند
- [x] edit/retry/report revision/rating semantics و canonical equality مشخص‌اند
- [x] delete/expiry/in-flight late result بدون resurrection طراحی شده است
- [x] latest-state-only و embedded-vs-relational tradeoff توجیه شده است
- [x] backup lifecycle به‌عنوان production gate باز و بدون وعده حذف فوری ثبت شده است

## AI and verification

- [x] provider-neutral seam کوچک است و provider registry/agent framework ندارد
- [x] evidence ID و content/type compatibility هر دو validate می‌شوند
- [x] timeout/schema/unsupported/stale paths limited یا discard مشخص دارند
- [x] provider/model/time/cost/evaluation پیش از live adapter gate هستند
- [x] unit/API/integration/frontend/browser/deployment verification تفکیک شده‌اند
- [x] browser exploration جانشین automated test نشده است

## Phase boundary

- [x] plan artifacts ایجاد شده‌اند؛ `tasks.md` ایجاد نشده است
- [x] application scaffold/dependency/browser runtime/code-intelligence tool نصب نشده است
- [x] tooling triggerها و future evaluationها explicit هستند

## Result

هیچ blocker فنی یا تعارض constitution برای رفتن به review برنامه دیده نشد. این checklist کیفیت specification/plan را
می‌سنجد و evidence اجرای application نیست.
