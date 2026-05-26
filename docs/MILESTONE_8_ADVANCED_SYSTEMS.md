# Milestone 8: Advanced Cloud Systems Extensions

This milestone upgrades GreenScale from a deterministic carbon-aware scheduler into a research platform for comparing multi-objective, reinforcement-learning, and autoscaling-aware placement policies.

## Added capabilities

1. **Scheduler policy modes**
   - `weighted`: existing latency/cost/carbon/cold-start weighted objective.
   - `pareto`: Pareto-front filtering followed by weighted tie-breaking.
   - `rl`: epsilon-greedy online reinforcement-learning layer over the weighted scheduler.

2. **Reinforcement-learning scheduler**
   - State: workload, priority, SLO bucket, and deadline presence.
   - Action: selected cloud region.
   - Reward: positive for low latency, SLO compliance, lower carbon, lower cost, and warm starts.
   - Endpoint: `GET /scheduler/qtable` exports the learned Q-table.

3. **Real autoscaling support**
   - HPA objects already exist for orchestrator and workers.
   - Metrics Server install scripts are included for Kind and managed Kubernetes.
   - VPA recommendation manifests are included in `k8s/vpa/vpa.yaml` with `updateMode: Off` so recommendations can be collected without automatically changing resources.

4. **Carbon API integration**
   - GreenScale uses static regional carbon metadata by default.
   - If `ELECTRICITY_MAPS_TOKEN` is provided, the orchestrator queries live zone-level carbon intensity with TTL caching.

5. **Helm chart**
   - `helm/greenscale` packages orchestrator, workers, HPA, Prometheus, and Grafana.
   - Values-driven configuration supports registry-backed images and scheduler policy selection.

6. **CI/CD**
   - `.github/workflows/advanced-ci.yml` validates Python tests, Kubernetes YAML, Helm chart linting, and Docker image builds.
   - Manual workflow dispatch can publish images to GitHub Container Registry.

7. **Baseline comparison**
   - `scripts/windows_run_baseline_comparison.ps1` compares weighted, latency-only, carbon-only, cost-only, Pareto, and RL policies.

## Scheduler policy switching

PowerShell:

```powershell
.\scripts\windows_set_scheduler_policy.ps1 -Policy weighted
.\scripts\windows_set_scheduler_policy.ps1 -Policy pareto
.\scripts\windows_set_scheduler_policy.ps1 -Policy rl
```

Bash:

```bash
./scripts/set_scheduler_policy.sh weighted
./scripts/set_scheduler_policy.sh pareto
./scripts/set_scheduler_policy.sh rl
```

## Metrics Server installation

PowerShell:

```powershell
.\scripts\windows_install_metrics_server.ps1
kubectl top pods -n greenscale
kubectl -n greenscale get hpa
```

Bash:

```bash
./scripts/install_metrics_server.sh
kubectl top pods -n greenscale
kubectl -n greenscale get hpa
```

## Helm deployment

```powershell
.\scripts\windows_helm_deploy.ps1 `
  -OrchestratorRepository YOUR_DOCKERHUB_USERNAME/greenscale-orchestrator `
  -WorkerRepository YOUR_DOCKERHUB_USERNAME/greenscale-worker `
  -Tag v1 `
  -Policy pareto
```

## Baseline comparison

```powershell
kubectl -n greenscale port-forward svc/greenscale-orchestrator 8080:8080
```

Then in another terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_run_baseline_comparison.ps1 -BaseUrl http://localhost:8080 -Iterations 10 -Concurrency 2
```

The output folder is created under `results/baselines_*`.

## Research interpretation

The baseline comparison enables the following research questions:

- How much carbon reduction is possible when latency is relaxed?
- How often does latency-only placement violate sustainability objectives?
- How does Pareto filtering differ from a scalar weighted objective?
- Does RL converge toward lower violation rates after repeated traffic?
- How does real HPA behavior affect observed latency and cold-start dynamics under load?
