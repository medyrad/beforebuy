#!/bin/sh
set -eu

: "${BEFOREBUY_COMPOSE_PROJECT:?set the isolated restore project}"
: "${BEFOREBUY_PRODUCTION_ENV:?set BEFOREBUY_PRODUCTION_ENV}"
: "${BEFOREBUY_RESTORE_DUMP:?set BEFOREBUY_RESTORE_DUMP}"

test -f "$BEFOREBUY_RESTORE_DUMP"
docker compose --project-name "$BEFOREBUY_COMPOSE_PROJECT" --env-file "$BEFOREBUY_PRODUCTION_ENV" \
  -f compose.production.yaml up -d --wait db
docker compose --project-name "$BEFOREBUY_COMPOSE_PROJECT" --env-file "$BEFOREBUY_PRODUCTION_ENV" \
  -f compose.production.yaml exec -T db sh -c \
  'exec pg_restore --exit-on-error --no-owner --no-acl --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  < "$BEFOREBUY_RESTORE_DUMP"
