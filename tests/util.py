import pytest

from fastapi.testclient import TestClient

from sean_gpt.main import app
from sean_gpt.util.describe import describe

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as client:
        yield client
