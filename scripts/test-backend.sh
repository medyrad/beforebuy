#!/bin/sh
set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

if [ -d /Applications/Docker.app/Contents/Resources/bin ]; then
    PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    export PATH
fi

if [ -f "$repository_root/.env" ]; then
    set -a
    # The development env file is project-local and uses shell-compatible KEY=value entries.
    . "$repository_root/.env"
    set +a
fi

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=${POSTGRES_HOST_PORT:-55439}
export POSTGRES_HOST POSTGRES_PORT

cd "$repository_root/backend"
exec uv run --project "$repository_root" python manage.py test tests --settings=config.settings.test "$@"
