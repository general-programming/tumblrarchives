#!/bin/sh
set -e

COMPOSEFILE="${0%/*}/../docker-compose.yml"
echo $SCRIPTDIR

docker-compose -f "$COMPOSEFILE" build --force-rm
docker-compose -f "$COMPOSEFILE" push
docker stack deploy -c "$COMPOSEFILE" --with-registry-auth tumblrarchives