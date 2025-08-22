#!/usr/bin/env bash
set -euo pipefail

missing=0

check_cmd() {
    local cmd="$1"
    local hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "$cmd not installed. $hint"
        missing=1
    fi
}

check_cmd docker "Install from https://docs.docker.com/get-docker/"
check_cmd pnpm "See https://pnpm.io/installation"

if command -v python3 >/dev/null 2>&1; then
    if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
        echo "python3 >=3.11 required. Install from your package manager or https://www.python.org/downloads/"
        missing=1
    fi
else
    echo "python3 not installed. Install from your package manager or https://www.python.org/downloads/"
    missing=1
fi

exit "$missing"
