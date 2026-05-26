#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID}"
REGION="${REGION:-us-central1}"
CLUSTER="${CLUSTER:-greenscale-gke}"
gcloud config set project "$PROJECT_ID"
gcloud container clusters create-auto "$CLUSTER" --region "$REGION"
gcloud container clusters get-credentials "$CLUSTER" --region "$REGION" --project "$PROJECT_ID"
kubectl get nodes
