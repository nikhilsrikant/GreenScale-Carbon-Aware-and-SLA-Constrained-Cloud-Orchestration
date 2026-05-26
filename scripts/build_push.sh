#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${1:-${REGISTRY:-ghcr.io/YOUR_USER}}"
TAG="${2:-${TAG:-dev}}"

docker build -t "$REGISTRY/greenscale-orchestrator:$TAG" ./orchestrator
docker build -t "$REGISTRY/greenscale-worker:$TAG" ./worker

docker push "$REGISTRY/greenscale-orchestrator:$TAG"
docker push "$REGISTRY/greenscale-worker:$TAG"

echo "Pushed images with tag $TAG to $REGISTRY"
