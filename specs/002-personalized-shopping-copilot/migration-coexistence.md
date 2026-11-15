# Feature 001 Coexistence and Migration

## Authorized bounded UX cutover — 2026-11-16

Product lead explicitly authorizes `/` as Shopping Copilot; `/copilot` remains compatible. `/legacy` preserves the
complete feature001 interface. Existing `/?analysis=<uuid>` and `/?view=history` still select LegacyApp, with ownership
and API paths unchanged. New legacy navigation uses `/legacy?...`. NGINX's existing `try_files ... /index.html`
already serves all three SPA paths; no proxy/production-routing policy change is necessary.

Rollback this UX by restoring the prior frontend route/image, without deleting data or reversing migration 0017.
Its two JSON columns are additive. Preserve backup and current credentials/keyring; do not restore a database over
active development data. Any DB restoration must use a separate new volume and reconcile spending/deletions first.
This authorizes default-route cutover only, not legacy retirement, public deployment or completion of Milestone E.

Feature 001، migrations، tests، reports و T039 historical evidence‌اند و overwrite/complete نمی‌شوند.

1. docs only (current): runtime unchanged.
2. foundation behind disabled route/flag؛ 001 unchanged.
3. internal fixture pilot؛ 001 default.
4. controlled pilot only after source/privacy/OpenAI/operations gates.
5. explicit product-lead cutover with rollback.
6. legacy retirement only via separate migration/export/deletion decision.

Analysis 001 خودکار به Conversation تبدیل نمی‌شود؛ user may explicitly import context with legacy attribution/unknowns. AvalAI config/T039 به OpenAI runtime migrate نمی‌شوند. 90-day policy universal نیست.

Rollback: route/flag to 001، stop 002 writes without deletion، no incompatible reverse migration، restore documented image/schema pair. Conversation 002 must not truncate into report 001.
