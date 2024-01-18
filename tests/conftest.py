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
import os

import pytest

from sean_gpt.util.describe import describe

from .fixtures.kubernetes import * # pylint: disable=wildcard-import disable=unused-wildcard-import
from .fixtures.auth import * # pylint: disable=wildcard-import disable=unused-wildcard-import

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture(scope="session")
def sean_gpt_host() -> str:

    # Monitor the api logs
    api_stern_process = subprocess.Popen(['stern', 'api-*', "-n", "seangpt", "--since", "1s"])
    env = os.environ['ENV'] if 'ENV' in os.environ else "local"

    # port-forward the Sean GPT deployment in the background
    seangpt_port_process = subprocess.Popen([
        "kubectl",
        "port-forward",
        "deployments/api",
        "--namespace",
        f"{env}-seangpt",
        "8000:8000"
    ])
    # wait for the port-forward to be ready
    time.sleep(2)

    yield "http://localhost:8000"

    seangpt_port_process.terminate()

    # Stop monitoring the logs
    api_stern_process.terminate()
