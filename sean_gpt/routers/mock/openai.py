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

chat_completion_patch = patch('openai.resources.chat.AsyncCompletions.create',
                              new=get_openai_stream)

def startup():
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    redis_conn.set("openai_response", "mocked response from openai")
    redis_conn.set("openai_response_delay", 0.1)
    redis_conn.set("latest_openai_request", json.dumps({'msg':"No request yet submitted"}))
    chat_completion_patch.start()

def shutdown():
    chat_completion_patch.stop()

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
    return

@router.get("/async_completions")
def get_openai_response():
    """ Mock OpenAI async completions endpoint."""
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    return {
        "response": redis_conn.get("openai_response").decode("utf-8"),
        "delay": float(redis_conn.get("openai_response_delay").decode("utf-8"))
    }

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

            return ChatCompletionChunk(
                choices=[Choice(delta=ChoiceDelta(content=char))],
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
