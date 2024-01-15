""" Application level and database level test fixtures.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe

from .fixtures.auth import * # pylint: disable=wildcard-import disable=unused-wildcard-import

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture(scope="session")
def sean_gpt_host() -> TestClient:
    # Monitor the kafka logs
    kafka_stern_process = subprocess.Popen(['stern',
                                            'seangpt-local-kafka-controller-*',
                                            "--since",
                                            "1s"])
    # Monitor the milvus logs
    milvus_stern_process = subprocess.Popen(['stern',
                                             'seangpt-local-milvus-standalone-*',
                                             "--since",
                                             "1s"])
    # Monitor the postgres logs
    postgres_stern_process = subprocess.Popen(['stern', 'postgres-*', "--since", "1s"])
    # Monitor the redis logs
    redis_stern_process = subprocess.Popen(['stern', 'redis-*', "--since", "1s"])
    # Monitor the sean-gpt logs
    sean_gpt_stern_process = subprocess.Popen(['stern', 'sean-gpt-*', "--since", "1s"])

    # port-forward the Sean GPT deployment in the background
    seangpt_port_process = subprocess.Popen([
        "kubectl",
        "port-forward",
        "deployments/sean-gpt",
        "8000:8000"
    ])
    # wait for the port-forward to be ready
    time.sleep(2)

    yield "http://localhost:8000"

    seangpt_port_process.terminate()

    # Stop monitoring the logs
    kafka_stern_process.terminate()
    milvus_stern_process.terminate()
    postgres_stern_process.terminate()
    redis_stern_process.terminate()
    sean_gpt_stern_process.terminate()
