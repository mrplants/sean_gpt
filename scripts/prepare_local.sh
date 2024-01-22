#!/bin/bash
set -e
set -x

pushd "$(cd "$(dirname "$0")" && pwd)"/..
trap 'popd' EXIT

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
    kind create cluster --name sean-gpt-local --config scripts/kind-config.yaml
fi

# Build and push the API
poetry export -f requirements.txt --output 'dist/requirements.txt' 
docker build -t sean_gpt_api:latest -f Dockerfile.local.api . 
kind load docker-image sean_gpt_api:latest -n sean-gpt-local

# Build and push the Database Migrator
docker build -t sean_gpt_migrate:latest -f Dockerfile.migrate .
kind load docker-image sean_gpt_migrate:latest -n sean-gpt-local
