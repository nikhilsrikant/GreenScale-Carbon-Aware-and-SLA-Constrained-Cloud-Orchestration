param(
    [ValidateSet("weighted", "pareto", "rl")]
    [string]$Policy = "weighted"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host "Setting GreenScale scheduler policy to '$Policy'..." -ForegroundColor Cyan
kubectl -n greenscale patch configmap greenscale-config --type merge -p "{`"data`":{`"SCHEDULER_POLICY`":`"$Policy`"}}"
kubectl -n greenscale rollout restart deployment/greenscale-orchestrator
kubectl -n greenscale rollout status deployment/greenscale-orchestrator --timeout=180s
Write-Host "Scheduler policy switched to '$Policy'." -ForegroundColor Green
