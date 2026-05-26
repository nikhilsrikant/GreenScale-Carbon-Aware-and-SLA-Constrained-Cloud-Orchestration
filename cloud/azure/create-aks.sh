#!/usr/bin/env bash
set -euo pipefail
RESOURCE_GROUP="${RESOURCE_GROUP:-greenscale-rg}"
LOCATION="${LOCATION:-eastus}"
CLUSTER="${CLUSTER:-greenscale-aks}"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
az aks create --resource-group "$RESOURCE_GROUP" --name "$CLUSTER" --node-count 2 --node-vm-size Standard_B2s --generate-ssh-keys
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$CLUSTER" --overwrite-existing
kubectl get nodes
