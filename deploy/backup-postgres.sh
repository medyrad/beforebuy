#!/bin/sh
set -eu

: "${BEFOREBUY_COMPOSE_PROJECT:?set BEFOREBUY_COMPOSE_PROJECT}"
: "${BEFOREBUY_PRODUCTION_ENV:?set BEFOREBUY_PRODUCTION_ENV}"
: "${BEFOREBUY_BACKUP_DIR:?set BEFOREBUY_BACKUP_DIR}"

umask 077
mkdir -p "$BEFOREBUY_BACKUP_DIR"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
target="$BEFOREBUY_BACKUP_DIR/beforebuy-$timestamp.dump"

docker compose --project-name "$BEFOREBUY_COMPOSE_PROJECT" --env-file "$BEFOREBUY_PRODUCTION_ENV" \
  -f compose.production.yaml exec -T db sh -c \
  'exec pg_dump --format=custom --no-owner --no-acl --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' > "$target"

find "$BEFOREBUY_BACKUP_DIR" -type f -name 'beforebuy-*.dump' -mtime +6 -delete
printf '%s\n' "$target"
