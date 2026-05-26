# Baseline Comparison Methodology

This project supports six scheduler baselines:

| Baseline | Policy | Interpretation |
|---|---|---|
| weighted_default | weighted | Original GreenScale weighted objective. |
| latency_only | weighted | Emulates a latency-minimizing scheduler. |
| carbon_only | weighted | Emulates a carbon-minimizing scheduler. |
| cost_only | weighted | Emulates a cost-minimizing scheduler. |
| pareto | pareto | Non-dominated multi-objective filtering. |
| rl | rl | Epsilon-greedy online reinforcement-learning policy. |

## Run baseline comparison

```powershell
kubectl -n greenscale port-forward svc/greenscale-orchestrator 8080:8080
```

In another terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_run_baseline_comparison.ps1 -BaseUrl http://localhost:8080 -Iterations 10 -Concurrency 2
```

## Suggested report metrics

- Mean latency and p95 latency.
- SLO violation rate.
- Dominant selected region.
- Region distribution entropy.
- Total estimated carbon.
- Total estimated cost.
- Cold-start rate.

## Expected research finding

Latency-only scheduling should reduce response time but may ignore carbon. Carbon-only scheduling may reduce estimated emissions but can violate strict SLOs. Pareto and RL policies should provide stronger trade-offs than single-objective baselines when workload classes differ.
