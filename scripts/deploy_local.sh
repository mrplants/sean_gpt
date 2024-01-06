#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e
set -x

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

# Build the project
poetry build

# Create requirements.txt and build the wheel
poetry export -f requirements.txt --output "$SCRIPT_DIR/../dist/requirements.txt"
LATEST_WHEEL=$(poetry run python "$SCRIPT_DIR/find_latest_whl.py" "$SCRIPT_DIR/../dist")
echo "Latest wheel: $LATEST_WHEEL"

# Build the API docker image and push to kind
docker build --build-arg WHEEL_FILE="$LATEST_WHEEL" -t sean_gpt_local:latest -f "$SCRIPT_DIR/../Dockerfile.api" "$SCRIPT_DIR/.."
kind load docker-image sean_gpt_local:latest -n sean-gpt-local
# Build the frontend docker image and push to kind
docker build -t sean_gpt_frontend_local:latest -f "$SCRIPT_DIR/../Dockerfile.frontend" "$SCRIPT_DIR/.."
kind load docker-image sean_gpt_frontend_local:latest -n sean-gpt-local

# Deploy the helm chart
helm upgrade --install seangpt-local "$SCRIPT_DIR/../sean_gpt_chart" \
    --values "$SCRIPT_DIR/../sean_gpt_chart/secrets.yaml" \
    --set sean_gpt.image=sean_gpt_local:latest \
    --set sean_gpt_frontend.image=sean_gpt_frontend_local:latest \
    --set local=true \
    --set postgres.storageClassName=standard \
    --set redis.storageClassName=standard \
    --kube-context kind-sean-gpt-local
