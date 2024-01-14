""" Test fixtures for Kubernetes.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
import subprocess
from pathlib import Path

import pytest

from sean_gpt.util.describe import describe

from .cluster_services import * # pylint: disable=wildcard-import disable=unused-wildcard-import

@describe(""" Test fixture for installing the sean_gpt chart. """)
@pytest.fixture(scope="session")
def sean_gpt_chart(): # pylint: disable=missing-function-docstring
    # Monitor the kafka logs
    kafka_stern_process = subprocess.Popen(['stern', 'seangpt-local-kafka-controller-*', "--since", "1s"])

    # Monitor the milvus logs
    milvus_stern_process = subprocess.Popen(['stern', 'seangpt-local-milvus-standalone-*', "--since", "1s"])

    # Monitor the postgres logs
    postgres_stern_process = subprocess.Popen(['stern', 'postgres-*', "--since", "1s"])

    # Monitor the redis logs
    redis_stern_process = subprocess.Popen(['stern', 'redis-*', "--since", "1s"])

    # Monitor the sean-gpt logs
    sean_gpt_stern_process = subprocess.Popen(['stern', 'sean-gpt-*', "--since", "1s"])

    # Install the chart using the deploy_local script
    deploy_script_path = Path(__file__).parent.parent.parent / "scripts/deploy_local.sh"
    subprocess.run([deploy_script_path], check=True)
    # Wait for the Kafka statefulset to be ready
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "statefulset",
        "seangpt-local-kafka-controller"
    ], check=True)

    # Wait for the Milvus deployment
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "deployment",
        "seangpt-local-milvus-standalone"
    ], check=True)

    # Wait for the Postgres statefulset
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "statefulset",
        "postgres"
    ], check=True)

    # Wait for the Redis statefulset
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "statefulset",
        "redis"
    ], check=True)

    # Wait for the Sean GPT deployment
    subprocess.run([
        "kubectl",
        "rollout",
        "status",
        "deployment",
        "sean-gpt"
    ], check=True)

    yield

    # Stop monitoring the logs
    kafka_stern_process.terminate()
    milvus_stern_process.terminate()
    postgres_stern_process.terminate()
    redis_stern_process.terminate()
    sean_gpt_stern_process.terminate()
