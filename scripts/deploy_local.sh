#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e
set -x

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# TODO: Build the frontend
# TODO: Copy the frontend into the static serving directory

# Build the project
poetry build

# Create requirements.txt and build the wheel
poetry export -f requirements.txt --output "$SCRIPT_DIR/../dist/requirements.txt"
LATEST_WHEEL=$(poetry run python "$SCRIPT_DIR/find_latest_whl.py" "$SCRIPT_DIR/../dist")
echo "Latest wheel: $LATEST_WHEEL"

# Build the docker image and push to kind
docker build --build-arg WHEEL_FILE="$LATEST_WHEEL" -t sean_gpt_local:latest "$SCRIPT_DIR/.."
kind load docker-image sean_gpt_local:latest

# Deploy the helm chart
helm upgrade --install seangpt-local "$SCRIPT_DIR/../sean_gpt_chart" \
    --values "$SCRIPT_DIR/../sean_gpt_chart/secrets.yaml" \
    --set sean_gpt.image=sean_gpt_local:latest \
    --set local=true \
    --set postgres.storageClassName=standard \
    --set redis.storageClassName=standard \
    --kube-context kind-kind
