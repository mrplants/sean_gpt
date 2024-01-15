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
    helm upgrade --install ingress-nginx ingress-nginx \
        --repo https://kubernetes.github.io/ingress-nginx \
        --namespace ingress-nginx --create-namespace
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
    # Access with:
    # $ kubectl proxy
    # http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
fi

# Build the frontend
pushd "$SCRIPT_DIR/../sean_gpt_frontend"
CI=true npm run build
popd

# Create requirements.txt and build the wheel
poetry export -f requirements.txt --output "$SCRIPT_DIR/../dist/requirements.txt"

# Build the API docker image and push to kind
docker build -t sean_gpt_local:latest -f "$SCRIPT_DIR/../Dockerfile.local.api" "$SCRIPT_DIR/.."
kind load docker-image sean_gpt_local:latest -n sean-gpt-local
# Build the frontend docker image and push to kind
docker build -t sean_gpt_frontend_local:latest -f "$SCRIPT_DIR/../Dockerfile.frontend" "$SCRIPT_DIR/.."
kind load docker-image sean_gpt_frontend_local:latest -n sean-gpt-local

# Deploy the helm chart
helm upgrade --install seangpt-local "$SCRIPT_DIR/../sean_gpt_chart" \
    --values "$SCRIPT_DIR/../sean_gpt_chart/test_secrets.yaml" \
    --set sean_gpt.image=sean_gpt_local:latest \
    --set sean_gpt_frontend.image=sean_gpt_frontend_local:latest \
    --set local=true \
    --kube-context kind-sean-gpt-local

# Run the database migrations
# First, wait for the database to be ready
kubectl rollout status statefulset postgres
# Port forward to the database
kubectl port-forward service/postgres 5432:5432 &
# Run the migrations
sean_gpt_database_host=localhost python -m alembic upgrade head
# Kill the port forward
kill %1