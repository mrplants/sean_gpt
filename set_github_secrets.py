#!/usr/bin/env python

import yaml
import subprocess

# Set the GitHub owner and repository
GH_OWNER = 'mrplants'
GH_REPO = 'sean_gpt'

# Get the directory of the script
SCRIPT_DIR = subprocess.run(['pwd'], capture_output=True, text=True).stdout.strip()

# Function to read and set secrets from a file
def set_secrets(secret_file):
    with open(f'{SCRIPT_DIR}/{secret_file}', 'r') as file:
        secrets = yaml.safe_load(file)['secrets']

    for name in secrets.keys():
        value = secrets[name]
        # Update the GitHub secret
        subprocess.run(['gh', 'secret', 'set', name, '--repos', f'{GH_OWNER}/{GH_REPO}'], input=str(value), text=True)

# Set secrets from secrets.yaml
set_secrets('secrets.yaml')