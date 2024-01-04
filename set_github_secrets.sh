#!/bin/bash

# Replace these variables with your repository and secret name
REPOSITORY="mrplants/sean_gpt"
SECRET_NAME="SECRETS_YAML"

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure the GitHub CLI and base64 are installed
if ! command -v gh &> /dev/null
then
    echo "GitHub CLI could not be found, please install it."
    exit
fi

# Check if secrets.yaml exists
if [ ! -f "$SCRIPT_DIR/sean_gpt_chart/secrets.yaml" ]; then
    echo "secrets.yaml not found."
    exit 1
fi

# Base64 encode the secrets.yaml file
ENCODED_SECRET=$(base64 < "$SCRIPT_DIR/sean_gpt_chart/secrets.yaml")

# Upload the secret using GitHub CLI
echo "Uploading secret to GitHub..."
gh secret set "$SECRET_NAME" --body "$ENCODED_SECRET" --repo "$REPOSITORY"

# Check if the upload was successful
if [ $? -eq 0 ]; then
    echo "Secret uploaded successfully."
else
    echo "Failed to upload secret."
    exit 1
fi
