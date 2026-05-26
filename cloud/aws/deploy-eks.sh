#!/usr/bin/env bash
set -euo pipefail
REGISTRY_NAMESPACE="${REGISTRY_NAMESPACE:?Set REGISTRY_NAMESPACE to your ECR, Docker Hub, or GHCR namespace}"
TAG="${TAG:-v1}"
eksctl create cluster -f cloud/aws/eksctl-greenscale.yaml
./scripts/build_push.sh "$REGISTRY_NAMESPACE" "$TAG"
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set images.orchestrator.repository="$REGISTRY_NAMESPACE/greenscale-orchestrator" \
  --set images.worker.repository="$REGISTRY_NAMESPACE/greenscale-worker" \
  --set images.orchestrator.tag="$TAG" \
  --set images.worker.tag="$TAG" \
  --set images.orchestrator.pullPolicy=Always \
  --set images.worker.pullPolicy=Always
kubectl -n greenscale rollout status deployment/greenscale-orchestrator --timeout=300s
