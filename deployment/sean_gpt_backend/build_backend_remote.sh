#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

poetry build
poetry export -f requirements.txt --output "$SCRIPT_DIR"/requirements.txt

cp "$SCRIPT_DIR"/../dist/*.whl "$SCRIPT_DIR"

docker build -t sean_gpt_backend "$SCRIPT_DIR"

# Load the image to the cluster
az acr login --name $(cd $SCRIPT_DIR/../terraform && terraform output -raw acr_name)
docker tag sean_gpt_backend:latest $(cd $SCRIPT_DIR/../terraform && terraform output -raw acr_login_server)/sean_gpt_backend:latest
docker push $(cd $SCRIPT_DIR/../terraform && terraform output -raw acr_login_server)/sean_gpt_backend:latest

kubectl delete replicaset fastapi-backend
kubectl apply -f "$SCRIPT_DIR/backend-set.yaml"