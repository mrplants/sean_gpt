""" Helper functions for chat tests. 
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

from unittest.mock import patch

from httpx_sse import connect_sse, aconnect_sse

from sean_gpt.util.describe import describe

from .mock import async_create_mock_streaming_openai_api

@describe(
""" Blocks and yields a streaming http response.

Args:
    request_type (str):  The request type.
    url (str):  The request URL.
    request_kwargs (dict):  Keyword arguments to pass to the client.
    client: The httpx client.
    
Yields:
    Chunks of text from the body of the response.
""")
def stream_response(url, request_kwargs, client, request_type='get'):
    with connect_sse(client, request_type.lower(), url, **request_kwargs) as event_source:
        print(event_source)
        for sse in event_source.iter_sse():
            yield sse.data

@describe(
""" Asynchronously yields a streaming http response.

Args:
    request_type (str):  The request type.
    url (str):  The request URL.
    request_kwargs (dict):  Keyword arguments to pass to the client.
    client: The httpx client.

Yields:
    Chunks of text from the body of the response.
""")
async def async_stream_response(request_type, url, request_kwargs, client):
    async with aconnect_sse(client, request_type.lower(), url, **request_kwargs) as event_source:
        async for sse in event_source.aiter_sse():
            yield sse.data

# pylint: disable=too-many-arguments
@describe(
""" Helper function to stream a long-running SSE response. """)
def stream_patched_delayed_response(
    patched_response,
    client,
    chat_id,
    access_token,
    delay,
    results_queue):
    with patch(
        'openai.resources.chat.AsyncCompletions.create',
        new=async_create_mock_streaming_openai_api(patched_response, delay=delay)):
        # Create a message.  The response will be streamed via SSE.
        request_kwargs = {
            "headers": {"Authorization": "Bearer " + access_token,
                        "X-Chat-ID": chat_id
                        },
            "json": {"content": "Hello, world! This is my first message in a chat."}
        }
        # The first message will be sent and then the response will be streamed.
        for event_data in stream_response("post","/chat/message/next",request_kwargs,client):
            results_queue.put(event_data)
# pylint: enable=too-many-arguments
