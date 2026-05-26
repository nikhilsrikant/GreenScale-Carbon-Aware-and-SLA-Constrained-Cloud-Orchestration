#!/usr/bin/env bash
set -euo pipefail
NAMESPACE="${NAMESPACE:-greenscale}"
ORCHESTRATOR_REPOSITORY="${ORCHESTRATOR_REPOSITORY:-greenscale-orchestrator}"
WORKER_REPOSITORY="${WORKER_REPOSITORY:-greenscale-worker}"
TAG="${TAG:-dev}"
POLICY="${POLICY:-weighted}"
helm lint ./helm/greenscale
helm upgrade --install greenscale ./helm/greenscale \
  --namespace "$NAMESPACE" --create-namespace \
  --set images.orchestrator.repository="$ORCHESTRATOR_REPOSITORY" \
  --set images.worker.repository="$WORKER_REPOSITORY" \
  --set images.orchestrator.tag="$TAG" \
  --set images.worker.tag="$TAG" \
  --set scheduler.policy="$POLICY"
kubectl -n "$NAMESPACE" rollout status deployment/greenscale-orchestrator --timeout=180s
kubectl -n "$NAMESPACE" get pods,svc,hpa
