#!/usr/bin/env bash
set -euo pipefail
POLICY="${1:-weighted}"
case "$POLICY" in
  weighted|pareto|rl) ;;
  *) echo "Usage: $0 [weighted|pareto|rl]" >&2; exit 2 ;;
esac
kubectl -n greenscale patch configmap greenscale-config --type merge -p "{\"data\":{\"SCHEDULER_POLICY\":\"$POLICY\"}}"
kubectl -n greenscale rollout restart deployment/greenscale-orchestrator
kubectl -n greenscale rollout status deployment/greenscale-orchestrator --timeout=180s
