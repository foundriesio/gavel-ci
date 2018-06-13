#!/bin/sh -ex

container="gavel-ci"
gl=$(git log -1 --pretty="format:%h %s")
hash=$(echo $gl | cut -d\  -f1)

# get jobserv version
gl="GavelCI: $gl
JobServ $(docker run --rm jobserv env | grep APP_VERSION | cut -d= -f2)"

echo "Building $container:$hash"
docker build --build-arg "GAVEL_VERSION=$gl" -t $container .
