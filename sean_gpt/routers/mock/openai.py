""" Mock OpenAI API for testing purposes.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

from unittest.mock import patch
import asyncio
from typing import Any
import json

from fastapi import APIRouter, Body
import redis

from ...config import settings

async def get_openai_stream(*args, **kwargs):
    """ Mocks the openai async chat completion endpoint.
    """
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    redis_conn.set("latest_openai_request",
                   json.dumps({'model':kwargs['model'], 'messages':kwargs['messages']}))
    openai_response = redis_conn.get("openai_response").decode("utf-8")
    delay = float(redis_conn.get("openai_response_delay").decode("utf-8"))
    print('Mock OpenAI request:', kwargs['messages'])
    print('Mock OpenAI response:', openai_response)
    return AsyncMockStream(openai_response, delay)

def get_random_embedding(*args, **kwargs):
    """ Mocks the openai embeddings endpoint.
    """
    print('Mock OpenAI embeddings request:', kwargs['input'])
    if isinstance(kwargs['input'], str):
        return {
            "object": "list",
            "data": [
                {
                "object": "embedding",
                "embedding": [0.0 for _ in range(1536)],
                "index": 0
                }
            ],
            "model": "text-embedding-ada-002",
            "usage": {
                "prompt_tokens": 8,
                "total_tokens": 8
            }
        }
    # The input is a list of strings
    # So return a list of embeddings that matches the length of the input
    return {
        "object": "list",
        "data": [
            {
            "object": "embedding",
            "embedding": [0.0 for _ in range(1536)],
            "index": i
            } for i in range(len(kwargs['input']))
        ],
        "model": "text-embedding-ada-002",
        "usage": {
            "prompt_tokens": 8,
            "total_tokens": 8
        }
    }

embeddings_patch = patch('openai.resources.Embeddings.create',
                        new=get_random_embedding)

chat_completion_patch = patch('openai.resources.chat.AsyncCompletions.create',
                              new=get_openai_stream)

def startup():
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    redis_conn.set("openai_response", "mocked response from openai")
    redis_conn.set("openai_response_delay", 0.1)
    redis_conn.set("latest_openai_request", json.dumps({'msg':"No request yet submitted"}))
    chat_completion_patch.start()
    embeddings_patch.start()

def shutdown():
    chat_completion_patch.stop()
    embeddings_patch.stop()

router = APIRouter(prefix="/mock/openai")

@router.get("/async_completions/call_args")
def get_openai_request():
    """ Retrieves the most recently sent SMS."""
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    return json.loads(redis_conn.get("latest_openai_request").decode("utf-8"))

@router.post("/async_completions")
def post_openai_response(*, response: str = Body(...),
                        delay: float = Body(...)):
    """ Mock OpenAI async completions endpoint."""
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    redis_conn.set("openai_response", response)
    redis_conn.set("openai_response_delay", delay)

@router.get("/async_completions")
def get_openai_response():
    """ Mock OpenAI async completions endpoint."""
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    return {
        "response": redis_conn.get("openai_response").decode("utf-8"),
        "delay": float(redis_conn.get("openai_response_delay").decode("utf-8"))
    }

class ChoiceDelta: # pylint: disable=too-few-public-methods
    """ Mocks the ChoiceDelta class from the OpenAI API. """
    def __init__(self, content='', role=None):
        self.content = content
        self.role = role
        self.tool_calls = None

class Choice: # pylint: disable=too-few-public-methods
    """ Mocks the Choice class from the OpenAI API."""
    def __init__(self, delta, finish_reason=None):
        self.delta = delta
        self.finish_reason = finish_reason

class ChatCompletionChunk: # pylint: disable=too-few-public-methods
    """ Mocks the ChatCompletionChunk class from the OpenAI API."""
    def __init__(self, choices, created, model):
        self.choices = choices
        self.created = created
        self.model = model
        self.id = "mocked-id-stream"
        self.object = "chat.completion.chunk"

class AsyncMockStream:
    """ Mocks an asynchronous iterable that yields streaming API responses.
    """
    def __init__(self, content, delay):
        """ Initializes the mock stream."""
        self.content = content
        self.delay = delay
        self.index = 0

    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        """ Returns the mock stream. """
        return self

    def __aiter__(self):
        """ Returns the mock stream. """
        return self

    async def __anext__(self):
        """ Yields the next character in the mock stream. """
        if self.index < len(self.content):
            char = self.content[self.index]
            self.index += 1
            await asyncio.sleep(self.delay)

            return ChatCompletionChunk(
                choices=[Choice(delta=ChoiceDelta(content=char))],
                created=1234567890,
                model="gpt-4-mock")
        if self.index == len(self.content):
            self.index += 1

            return ChatCompletionChunk(
                choices=[Choice(delta=ChoiceDelta(content=''), finish_reason="stop")],
                created=1234567890,
                model="gpt-4-mock")
        raise StopAsyncIteration

def async_create_mock_streaming_openai_api(content, delay=0.1):
    """
    Creates a mock function for the OpenAI streaming API.

    This function will yield mock responses in a streaming manner, structured as
    ChatCompletionChunk, with content split character by character.

    Args:
        content (str): The content to be included in the mock response.
        delay (float): The delay between each character stream, in seconds.

    Returns:
        AsyncMockStream: An asynchronous iterable that yields streaming API responses.
    """
    return AsyncMockStream(content, delay)
