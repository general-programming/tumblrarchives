#!/bin/sh
set -e

COMPOSEFILE="${0%/*}/../docker-compose.yml"
VOLUMEDIR="${0%/*}/../"

docker-compose -f "$COMPOSEFILE" run --rm -v "$VOLUMEDIR:/src" web extras/shell.sh