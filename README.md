# GreenScale: Carbon-Aware and SLA-Constrained Cloud Orchestration

GreenScale is a cloud-native research prototype for carbon-aware, cost-aware, and service-level-objective-constrained workload orchestration across simulated multi-cloud regions. The system evaluates how workload placement decisions can be made by jointly considering latency, estimated carbon intensity, execution cost, cold-start risk, and application-level service constraints.

The project is designed as cloud computing systems prototype. It includes a containerized orchestration layer, regional worker services, Kubernetes deployment manifests, observability through Prometheus and Grafana, automated experiment execution, baseline comparison tooling, and advanced scheduler extensions including Pareto-based multi-objective optimization and reinforcement-learning-based scheduling.

---

## 1. Project Objectives

The objective of GreenScale is to investigate the following research question:

> Can a cloud scheduler reduce estimated carbon impact and operational cost while preserving workload-specific latency service-level objectives?

GreenScale addresses this question through an end-to-end cloud-native implementation that supports:

- Multi-region workload routing
- SLA-aware scheduling
- Carbon-aware placement decisions
- Cost-aware placement decisions
- Cold-start-aware scheduling
- Kubernetes-based deployment
- Prometheus and Grafana observability
- Automated experimental evaluation
- Baseline comparison against alternative scheduling policies
- Registry-backed deployment workflow
- Helm and CI/CD deployment support

---

## 2. System Overview

GreenScale consists of an orchestrator service and multiple regional worker services. The orchestrator receives workload requests, evaluates candidate cloud regions, selects the most appropriate execution region using the configured scheduling policy, forwards the request to a worker, and records metrics for evaluation.

The worker services simulate geographically distributed cloud regions such as:

- `aws-us-east-1`
- `azure-westus`
- `gcp-us-central1`

Each region exposes the same workload interface but differs in synthetic latency, cost, carbon intensity, and cold-start characteristics.

---

## 3. Architecture

```text
Client / Load Generator
        |
        v
GreenScale Orchestrator
        |
        |-- Weighted Scheduler
        |-- Pareto Scheduler
        |-- Reinforcement-Learning Scheduler
        |
        v
Regional Worker Services
   |         |          |
 AWS       Azure       GCP
 Worker    Worker      Worker
        |
        v
Prometheus Metrics + Grafana Dashboard
        |
        v
Experiment and Baseline Evaluation Pipeline
```

---

## 4. Core Components

### Orchestrator

The orchestrator is implemented using FastAPI. It exposes APIs for workload invocation, health checks, scheduler policy inspection, and Prometheus metrics.

Responsibilities:

- Accept workload requests
- Retrieve current region metadata
- Score candidate regions
- Select a target region
- Forward workload requests to worker services
- Emit scheduling, latency, carbon, cost, and SLO metrics

### Worker Services

Worker services simulate cloud-region execution environments. Each worker receives a workload request, executes a synthetic workload-specific delay, optionally simulates cold-start behavior, and returns execution metadata.

Supported workload types include:

- Text classification
- ML inference
- Image compression
- Stream aggregation

### Observability Stack

The observability stack includes:

- Prometheus for metric scraping
- Grafana for dashboard visualization
- Kubernetes metrics through Metrics Server
- HPA visibility through `kubectl top` and Kubernetes autoscaling APIs

### Experiment Framework

The experiment framework executes repeatable workload scenarios and stores results in structured formats:

- CSV
- JSONL
- Markdown summaries
- Result charts

---

## 5. Scheduling Policies

GreenScale supports multiple scheduling policies.

### Weighted Multi-Objective Scheduler

The default scheduler computes a normalized score for each candidate region:

```text
Score(region) =
    alpha * latency_score
  + beta  * cost_score
  + gamma * carbon_score
  + delta * cold_start_score
```

The region with the lowest score is selected, subject to service-level constraints.

### Pareto Multi-Objective Scheduler

The Pareto scheduler identifies candidate regions that are non-dominated across multiple objectives, including latency, cost, carbon, and cold-start risk. It then selects a region from the Pareto frontier using a deterministic ranking strategy.

### Reinforcement-Learning Scheduler

The reinforcement-learning scheduler models scheduling as a state-action problem. It updates a Q-table using observed scheduling outcomes and reward signals derived from latency, carbon impact, cost, and SLO violations.

The reward function penalizes:

- High latency
- Estimated carbon impact
- Estimated execution cost
- SLO violations
- Cold-start risk

---

## 6. Repository Structure

```text
greenscale/
  orchestrator/          FastAPI-based scheduling and routing service
  worker/                Regional workload execution service
  experiments/           Experiment runner, scenario definitions, analysis tools
  loadtest/              Locust-based load testing
  k8s/                   Kubernetes manifests for local and cloud deployment
  k8s/vpa/               VPA recommendation manifests
  observability/         Prometheus and Grafana configuration
  helm/                  Helm chart for GreenScale
  cloud/                 Cloud-provider deployment starter files
  scripts/               Windows and shell automation scripts
  docs/                  Technical documentation and milestone notes
  tests/                 Unit tests for scheduler behavior
  data/                  Sample carbon-intensity input data
  .github/               GitHub Actions CI/CD workflows
```

---

## 7. Local Deployment with Docker Compose

### Prerequisites

- Docker Desktop
- Python 3.12 or later
- Git

### Run locally

```powershell
cd C:\Users\kulka\Downloads\greenscale
copy .env.example .env
docker compose up --build
```

### Health check

```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get | ConvertTo-Json -Depth 10
```

### Example workload request

```powershell
$body = @{
    payload = @{
        text = "cloud computing research workload"
    }
    slo_ms = 450
    priority = "latency-critical"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri "http://localhost:8080/invoke/text-classify" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body | ConvertTo-Json -Depth 20
```

---

## 8. Kubernetes Deployment with Kind

### Prerequisites

- Docker Desktop
- kubectl
- kind

### Create a local Kubernetes cluster

```powershell
kind create cluster --name greenscale --config .\k8s\kind-config.yaml
kubectl config use-context kind-greenscale
```

### Deploy GreenScale

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_run_milestone4.ps1
```

### Port-forward services

```powershell
kubectl -n greenscale port-forward svc/greenscale-orchestrator 8080:8080
kubectl -n greenscale port-forward svc/grafana 3000:3000
kubectl -n greenscale port-forward svc/prometheus 9090:9090
```

---

## 9. Registry-Backed Deployment

GreenScale supports deployment using container images pushed to a registry such as Docker Hub, AWS Elastic Container Registry, Azure Container Registry, or Google Artifact Registry.

### Build and push images to Docker Hub

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_dockerhub_quickstart.ps1 -DockerHubUsername YOUR_DOCKERHUB_USERNAME -Tag v2
```

### Apply rendered cloud manifest

```powershell
kubectl apply -f .\k8s\rendered\greenscale-cloud.yaml
kubectl -n greenscale rollout status deployment/greenscale-orchestrator --timeout=180s
kubectl -n greenscale get pods
```

---

## 10. Metrics Server and Autoscaling

GreenScale includes Kubernetes Horizontal Pod Autoscaler manifests. To enable real CPU and memory metrics in Kind, Metrics Server must be installed and configured for local kubelet certificates.

### Verify Metrics Server

```powershell
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top pods -n greenscale
kubectl -n greenscale get hpa
```

Expected behavior after configuration:

```text
v1beta1.metrics.k8s.io   kube-system/metrics-server   True
```

HPA should report real CPU values instead of `<unknown>`.

---

## 11. Observability

Grafana is available at:

```text
http://localhost:3000
```

Default credentials:

```text
Username: admin
Password: greenscale
```

Prometheus is available at:

```text
http://localhost:9090
```

The dashboard visualizes:

- Request volume
- Region selection
- Estimated latency
- Estimated carbon impact
- Estimated cost
- SLO behavior
- Cold-start behavior
- Worker-level metrics

---

## 12. Experiments

### Run standard experiments

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$env:GREENSCALE_BASE_URL="http://localhost:8080"
.\scripts\windows_run_experiments.ps1
```

Generated outputs include:

```text
results/
  run_<timestamp>/
    experiment_results.csv
    raw_responses.jsonl
    summary.json
    summary.md
    charts/
```

### Run baseline comparison

```powershell
.\scripts\windows_run_baseline_comparison.ps1 -Iterations 30 -Concurrency 5
```

The baseline suite evaluates:

- Weighted default scheduling
- Latency-only scheduling
- Carbon-only scheduling
- Cost-only scheduling
- Pareto scheduling
- Reinforcement-learning scheduling

---

## 13. Helm Deployment

A Helm chart is included under:

```text
helm/greenscale/
```

Example deployment:

```powershell
helm upgrade --install greenscale .\helm\greenscale -n greenscale --create-namespace
```

The Helm chart provides a configurable deployment interface for Kubernetes-based environments.

---

## 14. CI/CD

GitHub Actions workflows are included under:

```text
.github/workflows/
```

The CI/CD configuration supports:

- Python test execution
- Docker image build workflows
- Registry-oriented deployment preparation

Repository maintainers should configure required registry credentials as GitHub Actions secrets before enabling production image publishing.

---

## 15. Cloud Deployment

GreenScale is designed to be portable to managed Kubernetes platforms, including:

- Amazon Elastic Kubernetes Service
- Azure Kubernetes Service
- Google Kubernetes Engine

Cloud deployment documentation is available in:

```text
docs/REAL_CLOUD_DEPLOYMENT.md
docs/CLOUD_COMMAND_CHEATSHEET.md
docs/CLOUD_COST_SAFETY.md
```

For cloud deployment, the recommended workflow is:

1. Create a managed Kubernetes cluster.
2. Push GreenScale images to a cloud-accessible container registry.
3. Render Kubernetes manifests with registry-backed image names.
4. Apply the manifests to the target cluster.
5. Configure observability, autoscaling, and cost controls.
6. Run experiments and collect metrics.

---

## 16. Testing

Run scheduler tests:

```powershell
python -m pytest -q
```

Or from a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\orchestrator\requirements.txt pytest
pytest -q
```

---

## 17. Research Evaluation Summary

Initial experiments executed five workload scenarios:

- Latency-critical text classification
- Delay-tolerant batch text processing
- Strict ML inference
- Balanced image processing
- Delay-tolerant stream aggregation

The evaluation collected:

- Selected region
- Scheduler score
- Observed latency
- p95 latency
- Estimated carbon impact
- Estimated cost
- Cold-start rate
- SLO violation rate

The results showed that GreenScale preserved SLOs for most moderate and delay-tolerant workloads, while strict ML inference exposed the need for more aggressive latency-aware scheduling and cold-start mitigation. This provides a foundation for future work in reinforcement learning, adaptive policy selection, and real-time carbon-intensity integration.

---

## 18. Security and Cost Considerations

This repository does not include private credentials, cloud access keys, kubeconfig files, or environment-specific secrets. Users should keep all credentials outside version control.

The following files and directories should not be committed:

```text
.env
.venv/
results/
*.zip
*.log
.kube/
```

When deploying to public cloud platforms, users should enable budget alerts, use small clusters for testing, and delete unused resources after experiments.

---

## 19. Limitations

The current implementation is a research prototype. Some values, such as carbon intensity and regional latency, may be simulated or configured statically unless connected to an external carbon-intensity API. Real-world deployment requires additional validation around network variability, cloud billing models, authentication, production security, and multi-region data governance.

---

## 20. Future Work

Planned extensions include:

- Real-time carbon-intensity API integration
- Adaptive reinforcement-learning policy tuning
- Larger workload traces
- Real multi-cloud deployment across AWS, Azure, and Google Cloud
- Integration with Vertical Pod Autoscaler recommendations
- Advanced SLO-aware admission control
- Energy-aware batch deferral
- Multi-objective optimization using constrained solvers
- Carbon-aware scheduling for edge-cloud environments

---

## 21. License

This project is intended for academic and research use. Add a repository license before using or distributing the software publicly.

---

## 22. Citation

If this project is used in academic work, cite it as a cloud systems prototype for carbon-aware and SLA-constrained workload orchestration.

```text
GreenScale: Carbon-Aware and SLA-Constrained Cloud Orchestration.
Research prototype for cloud-native multi-objective workload scheduling.
```
