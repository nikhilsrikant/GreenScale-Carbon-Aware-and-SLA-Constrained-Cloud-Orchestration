#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8080}"
ITERATIONS="${ITERATIONS:-10}"
CONCURRENCY="${CONCURRENCY:-2}"
ROOT="results/baselines_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ROOT"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r experiments/requirements.txt

run_one() {
  local name="$1" policy="$2" latency="$3" cost="$4" carbon="$5" cold="$6"
  echo "Running baseline $name..."
  kubectl -n greenscale patch configmap greenscale-config --type merge -p "{\"data\":{\"SCHEDULER_POLICY\":\"$policy\",\"SCHEDULER_ALPHA_LATENCY\":\"$latency\",\"SCHEDULER_BETA_COST\":\"$cost\",\"SCHEDULER_GAMMA_CARBON\":\"$carbon\",\"SCHEDULER_DELTA_COLDSTART\":\"$cold\"}}"
  kubectl -n greenscale rollout restart deployment/greenscale-orchestrator
  kubectl -n greenscale rollout status deployment/greenscale-orchestrator --timeout=180s
  .venv/bin/python experiments/run_experiments.py --base-url "$BASE_URL" --iterations "$ITERATIONS" --concurrency "$CONCURRENCY" --out-dir "$ROOT/$name" --analyze
}

run_one weighted_default weighted 0.45 0.20 0.25 0.10
run_one latency_only weighted 1.00 0.00 0.00 0.00
run_one carbon_only weighted 0.00 0.00 1.00 0.00
run_one cost_only weighted 0.00 1.00 0.00 0.00
run_one pareto pareto 0.45 0.20 0.25 0.10
run_one rl rl 0.45 0.20 0.25 0.10

echo "Baseline comparison complete: $ROOT"
