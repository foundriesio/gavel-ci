#!/bin/sh -ex

container="gavel-ci"
gl=$(git log -1 --pretty="format:%h %s")
hash=$(echo $gl | cut -d\  -f1)

echo "Building $container:$hash"
docker build --build-arg "GAVEL_VERSION=$gl" -t $container .
