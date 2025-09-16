#!/usr/bin/env bash
set -euo pipefail

docker compose build labs
exec docker compose run --rm labs
