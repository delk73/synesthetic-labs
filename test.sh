#!/usr/bin/env bash
set -euo pipefail

docker build -t synesthetic-labs:test .
docker run --rm synesthetic-labs:test
