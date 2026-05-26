param(
    [string]$Namespace = "greenscale",
    [string]$OrchestratorRepository = "greenscale-orchestrator",
    [string]$WorkerRepository = "greenscale-worker",
    [string]$Tag = "dev",
    [ValidateSet("weighted", "pareto", "rl")]
    [string]$Policy = "weighted"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

helm version
helm lint .\helm\greenscale
helm upgrade --install greenscale .\helm\greenscale `
    --namespace $Namespace --create-namespace `
    --set images.orchestrator.repository=$OrchestratorRepository `
    --set images.worker.repository=$WorkerRepository `
    --set images.orchestrator.tag=$Tag `
    --set images.worker.tag=$Tag `
    --set scheduler.policy=$Policy

kubectl -n $Namespace rollout status deployment/greenscale-orchestrator --timeout=180s
kubectl -n $Namespace get pods,svc,hpa
