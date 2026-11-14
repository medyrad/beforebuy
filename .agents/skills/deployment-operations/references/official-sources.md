# Official operational references

Checked 2026-11-14. Re-check version-sensitive details before changing pinned images or framework settings.

- Django 5.2 deployment checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- Django 5.2 settings, including `SECURE_PROXY_SSL_HEADER`: https://docs.djangoproject.com/en/5.2/ref/settings/
- Docker Compose service dependencies and health conditions: https://docs.docker.com/reference/compose-file/services/
- Docker Compose startup order: https://docs.docker.com/compose/how-tos/startup-order/
- Docker Compose secrets: https://docs.docker.com/compose/how-tos/use-secrets/
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- PostgreSQL 18 backup overview: https://www.postgresql.org/docs/18/backup.html
- `pg_dump`: https://www.postgresql.org/docs/18/app-pgdump.html
- `pg_restore`: https://www.postgresql.org/docs/18/app-pgrestore.html
- NGINX unprivileged image (Apache-2.0): https://github.com/nginx/docker-nginx-unprivileged

Project interpretation: the Compose network and gateway-owned forwarding headers define the proxy trust boundary; production TLS and host scheduler installation remain operator responsibilities outside a local rehearsal.
