#!/usr/bin/env bash
# Keep the original keyring mounted on every development Compose invocation.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${COPILOT_MASTER_KEYRING_PATH:?Set the existing absolute protected keyring path; do not generate a replacement}"
case "$COPILOT_MASTER_KEYRING_PATH" in
  /*) ;;
  *) echo 'Keyring path must be absolute.' >&2; exit 1 ;;
esac
if [[ ! -f "$COPILOT_MASTER_KEYRING_PATH" || ! -r "$COPILOT_MASTER_KEYRING_PATH" ]]; then
  echo 'Existing keyring is unavailable; no containers were changed.' >&2
  exit 1
fi
exec docker compose -f compose.yaml -f compose.copilot-secrets.yaml "$@"
