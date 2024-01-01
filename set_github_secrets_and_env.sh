#!/bin/bash

# Set the GitHub owner and repository
GH_OWNER=mrplants
GH_REPO=sean_gpt

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Function to read and set secrets from a file
set_secrets() {
    local secret_file="$1"
    while IFS= read -r line
    do
        # Skip lines that are empty or start with a #
        [[ -z "$line" || "$line" =~ ^# ]] && continue

        # Split the line into a name and a value
        IFS='=' read -ra parts <<< "$line"
        local name="${parts[0]}"
        local value="${parts[1]}"

        # Update the GitHub secret
        echo "$value" | gh secret set "$name" --repos="$GH_OWNER/$GH_REPO"
    done < "${SCRIPT_DIR}/${secret_file}"
}

# Set secrets from .env.db_secrets and .env.backend_secrets
set_secrets ".env.secrets"