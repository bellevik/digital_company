#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

compose() {
  docker compose "$@"
}

api_url() {
  local host="${1:-localhost}"
  printf 'http://%s:8000' "${host}"
}

