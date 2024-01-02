#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

poetry build
poetry export -f requirements.txt --output "$SCRIPT_DIR"/requirements.txt

cp "$SCRIPT_DIR"/../dist/*.whl "$SCRIPT_DIR"

docker build -t sean_gpt_backend "$SCRIPT_DIR"

kind load docker-image sean_gpt_backend

kubectl delete replicaset fastapi-backend
kubectl apply -f "$SCRIPT_DIR/backend-set.yaml"