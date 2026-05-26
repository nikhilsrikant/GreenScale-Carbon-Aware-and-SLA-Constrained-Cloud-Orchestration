# GreenScale Helm Chart

This chart deploys the GreenScale orchestrator, simulated cloud workers, HPA objects, Prometheus, and Grafana.

## Local Kind install

```bash
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace
```

## Registry-backed install

```bash
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set images.orchestrator.repository=YOUR_DOCKERHUB_USERNAME/greenscale-orchestrator \
  --set images.worker.repository=YOUR_DOCKERHUB_USERNAME/greenscale-worker \
  --set images.orchestrator.tag=v1 \
  --set images.worker.tag=v1 \
  --set images.orchestrator.pullPolicy=Always \
  --set images.worker.pullPolicy=Always
```

## Scheduler modes

```bash
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set scheduler.policy=weighted

helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set scheduler.policy=pareto

helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set scheduler.policy=rl
```

## Live carbon intensity

```bash
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set carbon.electricityMapsToken="$ELECTRICITY_MAPS_TOKEN"
```
