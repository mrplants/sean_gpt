""" Test fixtures for kubernetes.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

import os

from kubernetes import client, config

# Load the kube config
config.load_kube_config()

# Create a client for the Kubernetes API
v1 = client.CoreV1Api()

# Get the pods for the deployment
pods = v1.list_namespaced_pod(namespace="seangpt", label_selector="app=api")

# Get the first pod
pod = pods.items[0]

# Get the environment variables from the pod's spec
env_vars = pod.spec.containers[0].env

# Set the environment variables in your Python process
for env_var in env_vars:
    if env_var.value is None:
        os.environ[env_var.name] = ""
    else:
        os.environ[env_var.name] = env_var.value
