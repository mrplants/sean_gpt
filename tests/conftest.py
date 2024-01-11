""" Application level and database level test fixtures.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
import time
from unittest.mock import patch, Mock
import os
import random
import re

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import psycopg2
import docker
import redis

from sean_gpt.config import settings
from sean_gpt.main import app
from sean_gpt.util.describe import describe

# pylint: disable=too-many-arguments
def wait_for_db_to_be_ready(host, port, user, password, max_attempts=10, delay=1):
    """Waits for the database to be ready to accept connections."""
    attempts = 0
    while attempts < max_attempts:
        try:
            # Try to connect to the database
            with psycopg2.connect(
                dbname='postgres',
                user=user,
                password=password,
                host=host,
                port=port):
                return True  # Successfully connected
        except psycopg2.OperationalError:
            # Connection failed
            time.sleep(delay)
            attempts += 1
    raise RuntimeError("Database did not become ready in time")
# pylint: enable=too-many-arguments

def wait_for_redis_to_be_ready(host, port, max_attempts=10, delay=1):
    """Waits for Redis to be ready to accept connections."""
    attempts = 0
    while attempts < max_attempts:
        try:
            r = redis.Redis(host=host, port=port)
            r.ping()
            return True  # Successfully connected
        except redis.exceptions.ConnectionError:
            time.sleep(delay)
            attempts += 1
    raise RuntimeError("Redis did not become ready in time")

@pytest.fixture
def local_redis(monkeypatch):

    # Mock the database host to be localhost
    monkeypatch.setattr(settings, 'redis_host', 'localhost')

    docker_client = docker.from_env()
    container = docker_client.containers.run(
        "redis:latest",
        detach=True,
        ports={"6379/tcp": 6379}
    )

    # Wait for the container to be ready
    while True:
        container.reload()
        if container.status == "running":
            break
        time.sleep(0.5)

    # Wait for Redis to be ready
    if not wait_for_redis_to_be_ready('localhost', 6379):
        raise RuntimeError("Unable to connect to Redis")

    yield
    # Teardown code here
    container.stop()
    container.remove(v=True)

@describe(""" Test fixture to start a local postgres database. """)
@pytest.fixture
def local_postgres(request, monkeypatch):

    # Mock the database host to be localhost
    monkeypatch.setattr(settings, 'database_host', 'localhost')

    admin_user = "postgres"
    admin_password = "admin_password"
    docker_client = docker.from_env()
    container = docker_client.containers.run(
        "postgres:latest",
        detach=True,
        ports={"5432/tcp": 5432},
        environment={
            "POSTGRES_USER": admin_user,
            "POSTGRES_PASSWORD": admin_password,
            "API_DB_USER": settings.api_db_user,
            "API_DB_PASSWORD": settings.api_db_password,
            "DATABASE_NAME": settings.database_name
        },
        volumes={
            os.path.abspath(
                'sean_gpt_chart/files/postgres_init.sh'
            ): {'bind': '/docker-entrypoint-initdb.d/init.sh',
                'mode': 'ro'},
        }
    )

    # Wait for the database to be ready
    if not wait_for_db_to_be_ready('localhost', 5432, admin_user, admin_password):
        raise RuntimeError("Unable to connect to the database")

    yield
    # Teardown code here
    container.stop()
    # if not request.session.testsfailed:
    container.remove(v=True)

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture
def client(local_postgres, local_redis) -> TestClient:
    with TestClient(app) as client:
        yield client

@describe(
""" Test fixture to provide an async test client for the application. """)
@pytest_asyncio.fixture
async def async_client(local_postgres) -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@describe(""" Test fixture to mock the Twilio SMS function. """)
@pytest.fixture
def mock_twilio_sms_create(client: TestClient) -> Mock:
    with patch('twilio.rest.api.v2010.account.message.MessageList.create') as mock_message_create:
        yield mock_message_create

@describe(""" Test fixture to provide an admin auth token. """)
@pytest.fixture
def admin_auth_token(client: TestClient) -> str:
    # Generate a token
    response = client.post(
        "/user/token",
        data={
            "grant_type": "password",
            "username": settings.user_admin_phone,
            "password": settings.user_admin_password,
        },
    )
    return response.json()["access_token"]

@describe(""" Test fixture to provide an admin user. """)
@pytest.fixture
def admin_user(admin_auth_token: str, client: TestClient) -> dict:
    # Get the admin user
    response = client.get(
        "/user",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json() | {"access_token": admin_auth_token}

@describe(""" Test fixture to provide a valid referral code. """)
@pytest.fixture
def referral_code(admin_auth_token: str, client: TestClient) -> str:
    # Get a referral code
    response = client.get(
        "/user/referral_code",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json()["referral_code"]

@describe(""" Test fixture to provide a new user and their auth token. """)
@pytest.fixture
def new_user(referral_code: str, client: TestClient) -> dict:
    # Create a new user with random phone and password
    new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    new_user_password = f"test{random.randint(0, 1000000)}"
    response_user = client.post(
        "/user",
        json={
            "user": {
                "phone": new_user_phone,
                "password": new_user_password,
            },
            "referral_code": referral_code
        }
    )
    # Get the new user's auth token
    response_token = client.post(
        "/user/token",
        data={
            "grant_type": "password",
            "username": new_user_phone,
            "password": new_user_password,
        },
    )
    yield response_user.json() | response_token.json() | {"password": new_user_password}
    # Delete the new user as cleanup
    client.delete(
        "/user",
        headers={"Authorization": f"Bearer {response_token.json()['access_token']}"}
    )

@describe(""" Test fixture to provide a verified new user and their auth token. """)
@pytest.fixture
def verified_new_user(new_user: dict, mock_twilio_sms_create: Mock, client: TestClient) -> dict:
    # TODO: Re-enable this when Twilio campaign is ready
    # # Request new user verification code
    # client.post(
    #     "/user/request_phone_verification",
    #     headers={"Authorization": f"Bearer {new_user['access_token']}"}
    # )
    # # pylint: disable=no-member
    # code_message_regex = (settings.app_phone_verification_message
    #                       .format('(\\S+)')
    #                       .replace('.', '\\.'))
    # phone_verification_code = re.search(
    #     code_message_regex,
    #     mock_twilio_sms_create.call_args[1]["body"]
    # ).group(1)
    # # pylint enable=no-member
    # # Verify the user
    # client.put(
    #     "/user/is_phone_verified",
    #     headers={"Authorization": f"Bearer {new_user['access_token']}"},
    #     json={"phone_verification_code": phone_verification_code}
    # )
    yield new_user
