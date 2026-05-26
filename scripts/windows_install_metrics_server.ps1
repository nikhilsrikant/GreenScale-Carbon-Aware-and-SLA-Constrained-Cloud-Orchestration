$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host "Installing Kubernetes Metrics Server..." -ForegroundColor Cyan
kubectl apply -f "https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"

Write-Host "Patching Metrics Server for local Kind/self-signed kubelet certificates..." -ForegroundColor Cyan
kubectl -n kube-system patch deployment metrics-server --type=json -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s
Write-Host "Metrics Server rollout complete." -ForegroundColor Green
kubectl top nodes
