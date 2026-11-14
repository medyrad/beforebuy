#!/bin/sh
set -eu

deploy/backup-postgres.sh
docker compose --project-name "$BEFOREBUY_COMPOSE_PROJECT" --env-file "$BEFOREBUY_PRODUCTION_ENV" \
  -f compose.production.yaml run --rm api python backend/manage.py purge_expired_analyses
