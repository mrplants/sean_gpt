#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Read file content
SECRET_VALUE=$(cat "$SCRIPT_DIR/sean_gpt_chart/secrets.yaml")

# Use GitHub CLI to create or update the secret
gh secret set secrets_yaml --body "$SECRET_VALUE" --repo mrplants/sean_gpt