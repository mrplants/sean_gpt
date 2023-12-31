from typing import Any
import pytest
import pytest_asyncio
import time
from unittest.mock import patch, Mock
import asyncio

from httpx import AsyncClient
from fastapi.testclient import TestClient
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import docker
import redis

from sean_gpt.main import app
from sean_gpt.util.describe import describe
from sean_gpt.config import settings

def wait_for_db_to_be_ready(host, port, user, password, max_attempts=10, delay=1):
    """Waits for the database to be ready to accept connections."""
    attempts = 0
    while attempts < max_attempts:
        try:
            # Try to connect to the database
            with psycopg2.connect(dbname='postgres', user=user, password=password, host=host, port=port):
                return True  # Successfully connected
        except psycopg2.OperationalError:
            # Connection failed
            time.sleep(delay)
            attempts += 1
    raise RuntimeError("Database did not become ready in time")

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
def local_redis():
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
    container.remove()

@describe(""" Test fixture to start a local postgres database. """)
@pytest.fixture
def local_postgres(request):
    docker_client = docker.from_env()
    container = docker_client.containers.run(
        "postgres:latest",
        detach=True,
        ports={"5432/tcp": 5432},
        environment={
            "POSTGRES_USER": "admin_user",
            "POSTGRES_PASSWORD": "admin_password",
        },
    )

    # Wait for the container to be ready
    while True:
        container.reload()
        if container.status == "running":
            break
        time.sleep(0.5)

    # Wait for the database to be ready
    if not wait_for_db_to_be_ready('localhost', 5432, "admin_user", "admin_password"):
        raise RuntimeError("Unable to connect to the database")

    # Connect to the PostgreSQL server
    conn = psycopg2.connect(dbname='postgres', user="admin_user", password="admin_password", host='localhost')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Cursor to perform database operations
    cur = conn.cursor()

    # Create a new user
    cur.execute(f"CREATE USER {settings.api_db_user} WITH ENCRYPTED PASSWORD %s;", (settings.api_db_password,))

    # Create a new database
    cur.execute(f"CREATE DATABASE {settings.api_db_name};")

    conn.close()
    conn = psycopg2.connect(dbname=settings.api_db_name, user="admin_user", password="admin_password", host='localhost')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Grant the user the ability to create tables in the public schema
    cur.execute(f"GRANT CREATE ON SCHEMA public TO {settings.api_db_user};")

    # Close communication with the database
    cur.close()
    conn.close()
    yield
    # Teardown code here
    container.stop()
    # if not request.session.testsfailed:
    container.remove()

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

def create_mock_openai_api(content):
    # Use this like:
    def mock_openai_api(*args, **kwargs):
        """
        Mock function to simulate OpenAI API response.

        Args and kwargs are ignored as this is a static mock.
        """
        return {
            "id": "mocked-id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4-1106-preview",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "logprobs": None,
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18
            },
            "system_fingerprint": None
        }
    return mock_openai_api

def create_mock_streaming_openai_api(content, delay=0.1):
    """
    Creates a mock function for the OpenAI streaming API.

    This function will yield mock responses in a streaming manner, structured as ChatCompletionChunk,
    with content split character by character.

    Args:
        content (str): The content to be included in the mock response.

    Returns:
        function: A mock function that yields streaming API responses.
    """
    # Use this like:
    def mock_streaming_openai_api(*args, **kwargs):
        """
        Mock function to simulate the streaming OpenAI API response.

        Args and kwargs are ignored as this is a static mock.
        """
        class ChoiceDelta:
            def __init__(self, content='', role=None):
                self.content = content
                self.role = role

        class Choice:
            def __init__(self, delta):
                self.delta = delta

        class ChatCompletionChunk:
            def __init__(self, choices, created, model):
                self.choices = choices
                self.created = created
                self.model = model
                self.id = "mocked-id-stream"
                self.object = "chat.completion.chunk"

        # Simulate the initial role token
        yield ChatCompletionChunk(choices=[Choice(delta=ChoiceDelta(role='assistant'))], created=1234567890, model="gpt-4-mock")

        # Split the content into single characters to simulate streaming
        for char in content:
            time.sleep(delay)
            yield ChatCompletionChunk(choices=[Choice(delta=ChoiceDelta(content=char))], created=1234567890, model="gpt-4-mock")

    return mock_streaming_openai_api

class AsyncMockStream:
    def __init__(self, content, delay):
        self.content = content
        self.delay = delay
        self.index = 0

    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index < len(self.content):
            char = self.content[self.index]
            self.index += 1
            await asyncio.sleep(self.delay)

            class ChoiceDelta:
                def __init__(self, content='', role=None):
                    self.content = content
                    self.role = role

            class Choice:
                def __init__(self, delta):
                    self.delta = delta

            class ChatCompletionChunk:
                def __init__(self, choices, created, model):
                    self.choices = choices
                    self.created = created
                    self.model = model
                    self.id = "mocked-id-stream"
                    self.object = "chat.completion.chunk"

            return ChatCompletionChunk(choices=[Choice(delta=ChoiceDelta(content=char))], created=1234567890, model="gpt-4-mock")
        
        raise StopAsyncIteration

def async_create_mock_streaming_openai_api(content, delay=0.1):
    """
    Creates a mock function for the OpenAI streaming API.

    This function will yield mock responses in a streaming manner, structured as ChatCompletionChunk,
    with content split character by character.

    Args:
        content (str): The content to be included in the mock response.
        delay (float): The delay between each character stream, in seconds.

    Returns:
        AsyncMockStream: An asynchronous iterable that yields streaming API responses.
    """
    return AsyncMockStream(content, delay)
