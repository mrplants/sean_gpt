#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Function to delete a Kubernetes resource if it exists
delete_if_exists() {
    local resource_type=$1
    local resource_name=$2
    kubectl get "$resource_type" "$resource_name" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "Deleting $resource_type $resource_name"
        kubectl delete "$resource_type" "$resource_name"
    else
        echo "$resource_type $resource_name does not exist. Skipping delete."
    fi
}

# Delete ConfigMap and Secrets if they exist
delete_if_exists configmap sean-gpt-env
delete_if_exists secret sean-gpt-db-secrets

# Create ConfigMap and Secrets
kubectl create configmap env --from-env-file="${SCRIPT_DIR}/.env"
kubectl create secret generic secrets --from-env-file="${SCRIPT_DIR}/.env.secrets"