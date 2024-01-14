""" Application level and database level test fixtures.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
import time

import pytest
from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe

from .fixtures.auth import * # pylint: disable=wildcard-import disable=unused-wildcard-import
from .fixtures.kubernetes import * # pylint: disable=wildcard-import disable=unused-wildcard-import

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture(scope="session")
def sean_gpt_host(sean_gpt_chart) -> TestClient:
    # Reset the app
    reset_postgres()
    reset_redis()
    reset_sean_gpt()
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
