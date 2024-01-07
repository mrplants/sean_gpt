#!/bin/bash

# If running this in a github workflow, make sure to run this step beforehand
# - name: Login to GitHub Container Registry
#   run: echo "${{ secrets.GHCR_PAT }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin

# Access with:
# $ kubectl proxy
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

pushd "$SCRIPT_DIR"

# Ensure popd is called on exit
trap popd EXIT

# Build the frontend
cd ../sean_gpt_frontend
REACT_APP_API_ENDPOINT=https://api.dev.sean-gpt.com CI=true npm run build

# Build the project
cd ..
poetry build

# Create requirements.txt and build the wheel
poetry export -f requirements.txt --output dist/requirements.txt
LATEST_WHEEL=$(poetry run python scripts/find_latest_whl.py dist)
echo "Latest wheel: $LATEST_WHEEL"

# Build the API docker image and push to GHCR
docker build --platform=linux/amd64 --build-arg WHEEL_FILE="$LATEST_WHEEL" -t ghcr.io/mrplants/sean_gpt_dev:latest -f Dockerfile.api .
docker push ghcr.io/mrplants/sean_gpt_dev:latest

# Build the frontend docker image and push to github dev
docker build --platform=linux/amd64 -t ghcr.io/mrplants/sean_gpt_frontend_dev:latest -f Dockerfile.frontend .
docker push ghcr.io/mrplants/sean_gpt_frontend_dev:latest

# Deploy the helm chart
cd sean_gpt_chart
helm upgrade --install seangpt-dev . \
    --values secrets.yaml \
    --set sean_gpt.image=ghcr.io/mrplants/sean_gpt_dev:latest \
    --set sean_gpt_frontend.image=ghcr.io/mrplants/sean_gpt_frontend_dev:latest \
    --set domain=dev.sean-gpt.com \
    --set api_domain=api.dev.sean-gpt.com \
    --set cert_prefix=sean-gpt-dev \
    --kube-context sean-gpt-aks \
    --namespace dev \
    --create-namespace