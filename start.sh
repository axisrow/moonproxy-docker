#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "Docker Engine and Docker Compose v2 are required." >&2
  exit 1
fi

mkdir -p config data logs trace
if [ ! -f config/config.yml ]; then
  cp config/config.example.yml config/config.yml
  echo "Created config/config.yml. Set proxy.anthropic.api_key, then run ./start.sh again." >&2
  exit 1
fi

if grep -q 'REPLACE_WITH_YOUR_ZAI_API_KEY' config/config.yml; then
  echo "Set proxy.anthropic.api_key in config/config.yml before starting." >&2
  exit 1
fi

docker compose up -d --build
docker compose exec moonbridge /app/moonbridge -config /config/config.yml -print-addr
