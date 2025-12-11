#!/bin/bash

# Stop script on first error
set -e

echo "=========================================="
echo " 5G Simulator - Deployment Script"
echo "=========================================="

# 1. Apply Namespace
echo "▶ Applying namespace..."
if [ -f "deploy/base/namespace.yaml" ]; then
    kubectl apply -f deploy/base/namespace.yaml
else
    kubectl create namespace pdc-nsd --dry-run=client -o yaml | kubectl apply -f -
fi

# 2. Deploy all resources using standalone Kustomize
echo "▶ Deploying all Kubernetes resources using Kustomize..."
kustomize build . | kubectl apply -f -

echo "=========================================="
echo "✅ Deployment completed successfully!"
echo "=========================================="
