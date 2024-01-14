""" Test fixtures for cluster services. """
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
import subprocess

import pytest

from sean_gpt.util.describe import describe

@describe(""" Test fixture for resetting a redis statefulset. """)
def reset_redis(): # pylint: disable=missing-function-docstring
    # Scale down the redis StatefulSet to 0 replicas
    subprocess.run([
        "kubectl",
        "scale",
        "statefulset/redis",
        "--replicas=0",
    ], check=True)

    # Delete the redis Pods and PVCs
    subprocess.run([
        "kubectl",
        "delete",
        "pods",
        "redis-0",  # Replace with the correct label selector for your Pods
    ], check=True)
    subprocess.run([
        "kubectl",
        "delete",
        "pvc",
        "redis-data-redis-0",  # Replace with the correct label selector for your PVCs
    ], check=True)

    # Scale up the redis StatefulSet back to its original number of replicas
    subprocess.run([
        "kubectl",
        "scale",
        "statefulset/redis",
        "--replicas=1",  # Replace with the original number of replicas
    ], check=True)

    # Wait for the Redis statefulset
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "statefulset",
        "redis"
    ], check=True)


@describe(""" Test fixture for resetting a postgres statefulset. """)
def reset_postgres(): # pylint: disable=missing-function-docstring
    # Scale down the postgres StatefulSet to 0 replicas
    subprocess.run([
        "kubectl",
        "scale",
        "statefulset/postgres",
        "--replicas=0",
    ], check=True)

    # Delete the postgres Pods and PVCs
    subprocess.run([
        "kubectl",
        "delete",
        "pods",
        "postgres-0",  # Replace with the correct label selector for your Pods
    ], check=True)
    subprocess.run([
        "kubectl",
        "delete",
        "pvc",
        "postgres-volume-postgres-0",  # Replace with the correct label selector for your PVCs
    ], check=True)

    # Scale up the postgres StatefulSet back to its original number of replicas
    subprocess.run([
        "kubectl",
        "scale",
        "statefulset/postgres",
        "--replicas=1",  # Replace with the original number of replicas
    ], check=True)

    # Wait for the Redis statefulset
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "statefulset",
        "postgres"
    ], check=True)

@describe(""" Test fixture for resetting a sean-gpt deployment. """)
def reset_sean_gpt():
    # Scale down the sean-gpt Deployment to 0 replicas
    subprocess.run([
        "kubectl",
        "scale",
        "deployment/sean-gpt",
        "--replicas=0",
    ], check=True)

    # Scale up the sean-gpt Deployment back to its original number of replicas
    subprocess.run([
        "kubectl",
        "scale",
        "deployment/sean-gpt",
        "--replicas=1",  # Replace with the original number of replicas
    ], check=True)

    # Wait for the sean-gpt deployment
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "deployment",
        "sean-gpt"
    ], check=True)
