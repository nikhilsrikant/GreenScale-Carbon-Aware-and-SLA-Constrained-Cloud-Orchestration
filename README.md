# GreenScale: Carbon-Aware, SLA-Constrained Cloud Orchestrator

GreenScale is a PhD-level cloud computing MVP for experimenting with carbon-aware, SLA-constrained workload placement across cloud regions/providers. It is intentionally cloud-agnostic: the same code can run locally with Docker Compose, on a single Kubernetes cluster, or across managed Kubernetes services such as AWS EKS, Azure AKS, and Google GKE.

## What this repository contains

- `orchestrator/`: FastAPI control plane that scores candidate regions and routes requests.
- `worker/`: FastAPI workload executor representing a cloud region/provider.
- `loadtest/`: Locust load generator.
- `k8s/`: Kubernetes manifests for EKS, AKS, GKE, Minikube, or Kind.
- `tests/`: unit tests for the scheduling logic.
- `data/`: sample carbon-intensity data.

## Research goal

Evaluate whether a multi-objective scheduler can reduce estimated carbon impact and cost while preserving latency SLOs for serverless/containerized workloads.

The current scheduler minimizes:

```text
score = alpha * normalized_latency
      + beta  * normalized_cost
      + gamma * normalized_carbon
      + delta * normalized_cold_start_risk
      + SLO_penalty
```

## Local quick start

```bash
cp .env.example .env
docker compose up --build
```

In another terminal:

```bash
curl -s http://localhost:8080/health | jq
curl -s -X POST http://localhost:8080/invoke/text-classify \
  -H 'Content-Type: application/json' \
  -d '{"payload":{"text":"cloud computing research workload"},"slo_ms":450}' | jq
```

Try stricter latency:

```bash
curl -s -X POST http://localhost:8080/invoke/ml-inference \
  -H 'Content-Type: application/json' \
  -d '{"payload":{"samples":256},"slo_ms":180,"priority":"latency-critical"}' | jq
```

Prometheus metrics:

```bash
curl http://localhost:8080/metrics
```

## Run tests locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r orchestrator/requirements.txt pytest
pytest -q
```

## Load test

```bash
docker compose --profile loadtest up --build locust
```

Open Locust at http://localhost:8089 and target `http://orchestrator:8080` from inside Docker, or `http://localhost:8080` from your host.

## Kubernetes deployment

For Minikube or Kind, build images locally and load them into the cluster, then apply manifests:

```bash
# Example with kind
kind create cluster --name greenscale

docker build -t greenscale-orchestrator:dev ./orchestrator
docker build -t greenscale-worker:dev ./worker
kind load docker-image greenscale-orchestrator:dev --name greenscale
kind load docker-image greenscale-worker:dev --name greenscale

kubectl apply -f k8s/
kubectl -n greenscale get pods
kubectl -n greenscale port-forward svc/greenscale-orchestrator 8080:8080
```

Then test:

```bash
curl -s -X POST http://localhost:8080/invoke/text-classify \
  -H 'Content-Type: application/json' \
  -d '{"payload":{"text":"hello cloud"},"slo_ms":500}' | jq
```

## Running on AWS/Azure/GCP

You can run this project on:

- AWS EKS
- Azure AKS
- Google Kubernetes Engine

Recommended PhD project path:

1. Start with Docker Compose to validate scheduler behavior.
2. Move to one managed Kubernetes cluster and simulate providers/regions as separate namespaces/services.
3. Move to real multi-region clusters.
4. Replace static carbon metadata with real grid/carbon traces.
5. Add RL/MPC scheduling as an advanced contribution.

## Environment variables

### Orchestrator

| Variable | Meaning |
|---|---|
| `REGION_ENDPOINTS` | JSON array of candidate regions/providers. |
| `STRICT_SLO` | If `true`, reject regions estimated to violate SLO unless all violate. |
| `SCHEDULER_ALPHA_LATENCY` | Latency weight. |
| `SCHEDULER_BETA_COST` | Cost weight. |
| `SCHEDULER_GAMMA_CARBON` | Carbon weight. |
| `SCHEDULER_DELTA_COLDSTART` | Cold-start risk weight. |
| `ELECTRICITY_MAPS_TOKEN` | Optional API token. Static metadata is used without it. |

### Worker

| Variable | Meaning |
|---|---|
| `REGION_NAME` | Worker region label. |
| `PROVIDER` | `aws`, `azure`, `gcp`, or custom. |
| `SIMULATED_LATENCY_MS` | Artificial execution/network latency. |
| `COLD_START_PROBABILITY` | Probability of a simulated cold start. |
| `COLD_START_MS` | Extra latency added on cold start. |

## Suggested experimental scenarios

- Latency-first policy: increase `SCHEDULER_ALPHA_LATENCY`.
- Carbon-first policy: increase `SCHEDULER_GAMMA_CARBON`.
- Cost-first policy: increase `SCHEDULER_BETA_COST`.
- Cold-start sensitivity: increase `SCHEDULER_DELTA_COLDSTART`.
- Failure experiment: stop one worker and observe failover.

## Next research extensions

- Add real-time carbon traces.
- Add deadline-aware deferral for batch workloads.
- Add a Kubernetes custom controller.
- Add multi-cluster service discovery.
- Add reinforcement learning policy training.
- Add privacy/data-residency constraints.

## Milestone 2: experiment automation and graphs

Milestone 2 adds repeatable experiments under `experiments/`.

Keep the Docker Compose stack running in one terminal:

```bash
docker compose up --build
```

Then run the experiment automation from another terminal.

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_run_milestone2.ps1
```

Linux, macOS, or WSL:

```bash
bash scripts/run_experiments.sh
```

Manual command:

```bash
python experiments/run_experiments.py \
  --base-url http://localhost:8080 \
  --out-dir results \
  --iterations 10 \
  --concurrency 2 \
  --analyze
```

Each run creates a timestamped folder under `results/` containing:

- `experiment_results.csv` for statistical analysis.
- `raw_responses.jsonl` for full traceability.
- `summary.json` for machine-readable metrics.
- `summary.md` for report writing.
- `charts/*.png` for report-ready figures.

The default scenarios are defined in `experiments/scenarios.json` and include latency-critical, balanced, and delay-tolerant workloads.

## Milestone 3: Observability

Start GreenScale with Prometheus and Grafana:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_run_milestone3.ps1
```

Open:

- Orchestrator: http://localhost:8080/health
- Prometheus: http://localhost:9090/targets
- Grafana: http://localhost:3000
- Grafana login: `admin` / `greenscale`

Then open the Grafana dashboard:

```text
Dashboards -> GreenScale -> GreenScale Cloud Observability
```

Detailed instructions are in `docs/MILESTONE_3_OBSERVABILITY.md`.

## Milestone 5: Registry and cloud deployment

GreenScale can now be prepared for a managed Kubernetes cluster by pushing images to a container registry and rendering cloud-ready manifests.

Docker Hub quickstart:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_dockerhub_quickstart.ps1 -DockerHubUsername YOUR_DOCKERHUB_USERNAME -Tag v1
kubectl apply -f .\k8s\rendered\greenscale-cloud.yaml
```

Provider-neutral flow:

```powershell
.\scripts\windows_build_push_registry.ps1 -RegistryNamespace REGISTRY_PREFIX -Tag v1
.\scripts\windows_render_cloud_manifests.ps1 -RegistryNamespace REGISTRY_PREFIX -Tag v1
kubectl apply -f .\k8s\rendered\greenscale-cloud.yaml
```

See:

```text
docs/MILESTONE_5_CLOUD_DEPLOYMENT.md
docs/CLOUD_COST_SAFETY.md
docs/CLOUD_COMMAND_CHEATSHEET.md
```

## Advanced research extensions

This repository now includes advanced cloud-systems extensions:

- Reinforcement-learning scheduler mode: `SCHEDULER_POLICY=rl`
- Pareto multi-objective scheduler mode: `SCHEDULER_POLICY=pareto`
- Live carbon-intensity integration through `ELECTRICITY_MAPS_TOKEN`
- Kubernetes Metrics Server install scripts for real HPA metrics
- VPA recommendation manifests under `k8s/vpa/`
- Helm chart under `helm/greenscale/`
- GitHub Actions CI/CD under `.github/workflows/advanced-ci.yml`
- Baseline comparison scripts for latency-only, carbon-only, cost-only, weighted, Pareto, and RL policies

See:

- `docs/MILESTONE_8_ADVANCED_SYSTEMS.md`
- `docs/REAL_CLOUD_DEPLOYMENT.md`
- `docs/BASELINE_COMPARISON.md`
