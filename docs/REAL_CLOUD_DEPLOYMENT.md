# Real AWS, Azure, and Google Cloud Deployment

GreenScale is Kubernetes-native. The same Helm chart or rendered YAML can be deployed to Amazon EKS, Azure AKS, or Google GKE after the images are pushed to a registry.

## Generic sequence

1. Create a managed Kubernetes cluster.
2. Push GreenScale images to a registry reachable by the cluster.
3. Install Metrics Server if it is not already available.
4. Deploy GreenScale using Helm or rendered YAML.
5. Port-forward or expose the orchestrator and Grafana.
6. Run smoke tests and experiments.
7. Delete cloud resources when finished.

## AWS EKS

Prerequisites: AWS CLI, eksctl, kubectl, Docker.

```bash
cd greenscale
export REGISTRY_NAMESPACE=YOUR_DOCKERHUB_USERNAME
export TAG=v1
eksctl create cluster -f cloud/aws/eksctl-greenscale.yaml
./scripts/build_push.sh "$REGISTRY_NAMESPACE" "$TAG"
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set images.orchestrator.repository=$REGISTRY_NAMESPACE/greenscale-orchestrator \
  --set images.worker.repository=$REGISTRY_NAMESPACE/greenscale-worker \
  --set images.orchestrator.tag=$TAG \
  --set images.worker.tag=$TAG \
  --set images.orchestrator.pullPolicy=Always \
  --set images.worker.pullPolicy=Always
```

Delete when done:

```bash
eksctl delete cluster --name greenscale --region us-east-1
```

## Azure AKS

Prerequisites: Azure CLI, kubectl, Docker.

```bash
cd greenscale
cloud/azure/create-aks.sh
export REGISTRY_NAMESPACE=YOUR_DOCKERHUB_USERNAME
export TAG=v1
./scripts/build_push.sh "$REGISTRY_NAMESPACE" "$TAG"
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set images.orchestrator.repository=$REGISTRY_NAMESPACE/greenscale-orchestrator \
  --set images.worker.repository=$REGISTRY_NAMESPACE/greenscale-worker \
  --set images.orchestrator.tag=$TAG \
  --set images.worker.tag=$TAG \
  --set images.orchestrator.pullPolicy=Always \
  --set images.worker.pullPolicy=Always
```

Delete when done:

```bash
az group delete --name greenscale-rg --yes --no-wait
```

## Google GKE

Prerequisites: gcloud CLI, kubectl, Docker.

```bash
cd greenscale
export PROJECT_ID=YOUR_GCP_PROJECT_ID
cloud/gcp/create-gke.sh
export REGISTRY_NAMESPACE=YOUR_DOCKERHUB_USERNAME
export TAG=v1
./scripts/build_push.sh "$REGISTRY_NAMESPACE" "$TAG"
helm upgrade --install greenscale ./helm/greenscale \
  --namespace greenscale --create-namespace \
  --set images.orchestrator.repository=$REGISTRY_NAMESPACE/greenscale-orchestrator \
  --set images.worker.repository=$REGISTRY_NAMESPACE/greenscale-worker \
  --set images.orchestrator.tag=$TAG \
  --set images.worker.tag=$TAG \
  --set images.orchestrator.pullPolicy=Always \
  --set images.worker.pullPolicy=Always
```

Delete when done:

```bash
gcloud container clusters delete greenscale-gke --region us-central1
```

## Cost controls

- Use small node types during experiments.
- Keep max nodes low.
- Use short experiments first.
- Delete clusters after use.
- Avoid public load balancers until necessary.
- Prefer port-forwarding for demonstrations.
