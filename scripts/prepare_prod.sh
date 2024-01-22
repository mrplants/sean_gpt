#!/bin/bash
set -e
set -x

pushd "$(cd "$(dirname "$0")" && pwd)"/..
trap 'popd' EXIT

# Build and push the API
poetry export -f requirements.txt --output 'dist/requirements.txt'
poetry build
LATEST_WHEEL=$(poetry run python scripts/get_latest_whl.py dist)
LATEST_VERSION=$(poetry run python scripts/get_version.py pyproject.toml)
docker build --platform=linux/amd64 --build-arg WHEEL_FILE=$LATEST_WHEEL -t ghcr.io/mrplants/sean_gpt_api:$LATEST_VERSION -f Dockerfile.api . 
docker tag ghcr.io/mrplants/sean_gpt_api:$LATEST_VERSION ghcr.io/mrplants/sean_gpt_api:latest
docker push ghcr.io/mrplants/sean_gpt_api:$LATEST_VERSION
docker push ghcr.io/mrplants/sean_gpt_api:latest

# Build and push the Database Migrator
docker build --platform=linux/amd64 -t ghcr.io/mrplants/sean_gpt_migrate:$LATEST_VERSION -f Dockerfile.migrate .
docker tag ghcr.io/mrplants/sean_gpt_migrate:$LATEST_VERSION ghcr.io/mrplants/sean_gpt_migrate:latest
docker push ghcr.io/mrplants/sean_gpt_migrate:$LATEST_VERSION
docker push ghcr.io/mrplants/sean_gpt_migrate:latest

# Build and push the frontend
cd sean_gpt_frontend
CI=true REACT_APP_API_ENDPOINT="https://api.sean-gpt.com" npm run build
cd ..
docker build --platform=linux/amd64 -t ghcr.io/mrplants/sean_gpt_frontend:$LATEST_VERSION -f Dockerfile.frontend .
docker tag ghcr.io/mrplants/sean_gpt_frontend:$LATEST_VERSION ghcr.io/mrplants/sean_gpt_frontend:latest
docker push ghcr.io/mrplants/sean_gpt_frontend:$LATEST_VERSION
docker push ghcr.io/mrplants/sean_gpt_frontend:latest