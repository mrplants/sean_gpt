""" Application level and database level test fixtures.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
from typing import Generator

import pytest

from sean_gpt.util.describe import describe

from .fixtures.kubernetes import * # pylint: disable=wildcard-import disable=unused-wildcard-import
from .fixtures.auth import * # pylint: disable=wildcard-import disable=unused-wildcard-import
from .util.kubernetes import monitor_logs, port_forward

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture(scope="session")
def sean_gpt_host() -> Generator[str, None, None]:

    with monitor_logs(), port_forward(8000):
        yield "http://localhost:8000"
