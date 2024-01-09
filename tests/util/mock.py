""" Mock functions for testing.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

import time
import asyncio
from typing import Any

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

#pylint: disable=too-few-public-methods
def create_mock_streaming_openai_api(content, delay=0.1):
    """
    Creates a mock function for the OpenAI streaming API.

    This function will yield mock responses in a streaming manner, structured as
    ChatCompletionChunk, with content split character by character.

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
        yield ChatCompletionChunk(
            choices=[Choice(delta=ChoiceDelta(role='assistant'))],
            created=1234567890,
            model="gpt-4-mock")

        # Split the content into single characters to simulate streaming
        for char in content:
            time.sleep(delay)
            yield ChatCompletionChunk(
                choices=[Choice(delta=ChoiceDelta(content=char))],
                created=1234567890,
                model="gpt-4-mock")

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

            return ChatCompletionChunk(
                choices=[Choice(delta=ChoiceDelta(content=char))],
                created=1234567890,
                model="gpt-4-mock")
        raise StopAsyncIteration
#pylint: enable=too-few-public-methods

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
