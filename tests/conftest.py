""" Application level and database level test fixtures.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
import os

import pytest

from sean_gpt.util.describe import describe

from .fixtures.kubernetes import * # pylint: disable=wildcard-import disable=unused-wildcard-import
from .fixtures.auth import * # pylint: disable=wildcard-import disable=unused-wildcard-import
from .util.kubernetes import monitor_logs, port_forward

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture(scope="session")
def sean_gpt_host() -> str:
    # Get the environment
    env = os.environ['ENV'] if 'ENV' in os.environ else "local"

    with monitor_logs(), port_forward(env, 8000):
        yield "http://localhost:8000"
