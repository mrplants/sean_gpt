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
docker build --platform=linux/amd64 --build-arg WHEEL_FILE=$LATEST_WHEEL -t ghcr.io/mrplants/sean_gpt_api:latest -f Dockerfile.api . 
docker push ghcr.io/mrplants/sean_gpt_api:$LATEST_VERSION
docker push ghcr.io/mrplants/sean_gpt_api:latest

# Build and push the Database Migrator
docker build --platform=linux/amd64 -t ghcr.io/mrplants/sean_gpt_migrate:$LATEST_VERSION -f Dockerfile.migrate .
docker build --platform=linux/amd64 -t ghcr.io/mrplants/sean_gpt_migrate:latest -f Dockerfile.migrate .
docker push ghcr.io/mrplants/sean_gpt_migrate:$LATEST_VERSION
docker push ghcr.io/mrplants/sean_gpt_migrate:latest

# Build and push the frontend
cd sean_gpt_frontend
CI=true npm run build
cd ..
docker build --platform=linux/amd64 -t ghcr.io/mrplants/sean_gpt_frontend:$LATEST_VERSION -f Dockerfile.frontend .
docker build --platform=linux/amd64 -t ghcr.io/mrplants/sean_gpt_frontend:latest -f Dockerfile.frontend .
docker push ghcr.io/mrplants/sean_gpt_frontend:$LATEST_VERSION
docker push ghcr.io/mrplants/sean_gpt_frontend:latest