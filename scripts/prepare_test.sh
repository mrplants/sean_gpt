#!/bin/bash
set -e
set -x

# Build and push the API
poetry export -f requirements.txt --output 'dist/requirements.txt'
poetry build
LATEST_WHEEL=$(poetry run python scripts/get_latest_whl.py dist)
docker build --build-arg WHEEL_FILE=$LATEST_WHEEL -t sean_gpt_api:latest -f Dockerfile.api . 
kind load docker-image sean_gpt_api:latest -n sean-gpt-local

# Build and push the Database Migrator
docker build -t sean_gpt_migrate:latest -f Dockerfile.migrate .
kind load docker-image sean_gpt_migrate:latest -n sean-gpt-local
