#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

function kind_cluster_exists() {
    local cluster_name="$1"
    kind get clusters | grep -q "^${cluster_name}$"
    return $?
}

# Create a fresh kind cluster for this deployment
if kind_cluster_exists "sean-gpt-local"; then
    echo "Cluster sean-gpt-local exists"
else
    echo "Cluster sean-gpt-local does not exist.  Creating..."
    kind create cluster --name sean-gpt-local --config "$SCRIPT_DIR/kind-config.yaml"
    # Access with:
    # $ kubectl proxy
    # http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
fi

# Deploy the helm chart
helmfile apply