######################
# /chat/message/next #
######################
# GET (protected, verified)
#   Get the next message in a chat. Chat UUID in header.
#
# This is implemented via SSE.  The client makes a POST request to push a new
# message to the chat.  The server begins streaming the AI response back to the
# client.  If the client makes another POST request, the server terminates the
# first SSE stream and then creates a new SSE stream for the new POST request.
#
# Importantly, the /chat/message/next endopint does not interact with the
# database.  It is simply a way to exchange messages with the assistant.  The
# database is updated when the client makes a POST request to /chat/message.

import time
from unittest.mock import patch, AsyncMock
import multiprocessing as mp
import threading as th
from queue import Queue

from sean_gpt.util.describe import describe

from ..user.fixtures import *
from ..fixtures import *
from .util import *

@describe(
""" Tests that a basic, uninterrupted message exchange can occur.

- Create a chat.
- Create a message in the chat.
- Receive the entire response without interruption (it is a stream).

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_create_message(verified_new_user: dict, client: TestClient):
    expected_response = "Streaming response."
    with patch('openai.resources.chat.AsyncCompletions.create', new_callable=Mock) as mock_openai_api:
        mock_openai_api.side_effect = async_create_mock_streaming_openai_api(expected_response, delay=0.001)
        # Create a chat
        chat = client.post("/chat",
                        headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                        json={}).json()
        # Create a message.  The response will be streamed via SSE.
        request_kwargs = {
            "headers": {"Authorization": "Bearer " + verified_new_user["access_token"],
                        "X-Chat-ID": chat["id"]
                        },
            "json": {"content": "Hello, world! This is my first message in a chat."}
        }
        assistant_response = ''.join(stream_response("post","/chat/message/next",request_kwargs,client))
    # The assistant response is just the string content, without the ID of the message.
    assert assistant_response == expected_response

@describe(
""" Tests that a chat is tracking when an assistant is responding.

is_assistant_responding should be True when the assistant is responding to a
message, and False when the assistant is not responding to a message.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_is_assistant_responding(verified_new_user: dict, client: TestClient):
    # Create a chat
    chat = client.post("/chat",
                    headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                    json={})
    chat = chat.json()
    expected_response = "123456789012345678901234567890" # 3 seconds of streaming at 0.1 seconds per character.
    results_queue = Queue()
    # - Send a message with a long running response in a separate process.
    message_request_process = th.Thread(
         target = stream_patched_delayed_response,
         args = (expected_response, client, chat["id"], verified_new_user["access_token"], 0.1, results_queue)
    )
    message_request_process.start()
    # - Wait until the middle of the resopnse, then check that the chat is marked
    # as responding.
    time.sleep(1)
    chat_check = client.get("/chat",
                    headers={"Authorization": "Bearer " + verified_new_user["access_token"]},
                    params={"id": chat["id"]}).json()[0]
    assert chat_check["is_assistant_responding"] == True, "Check that chat is marked as is_assistant_responding."
    # - Wait until the end of the response, then check that the chat is no longer
    # marked as responding.
    message_request_process.join()
    chat_check = client.get("/chat",
                    headers={"Authorization": "Bearer " + verified_new_user["access_token"]},
                    params={"id": chat["id"]}).json()[0]
    assert chat_check["is_assistant_responding"] == False, "Check that chat is no longer marked as is_assistant_responding."
    # - Check that the response is correct.
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    assert ''.join(results) == expected_response, "Check that the response is correct."

@describe(
""" Tests that chat messages are passed in order.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_message_order(verified_new_user: dict, client: TestClient):
    # Create a chat
    chat = client.post("/chat",
                    headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                    json={}).json()
    # Create a few messages for the chat.
    for message_i in range(settings.chat_history_length-1):
        client.post("/chat/message",
                headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                        "X-Chat-ID": chat["id"]
                        },
                json={"content": f"Message {message_i}",
                      "role": "user"})
    # Check that those messages are retrievable
    messages = client.get("/chat/message",
                    headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                             "X-Chat-ID": chat["id"]},
                    params={"limit": settings.chat_history_length-1, "offset": 0}).json()
    messages_contents = [message["content"] for message in messages]
    assert messages_contents == [f"Message {message_i}" for message_i in range(settings.chat_history_length-1)], "Check that the messages are retrievable."
    with patch('openai.resources.chat.AsyncCompletions.create', new_callable=Mock) as mock_openai_api:
        mock_openai_api.side_effect = async_create_mock_streaming_openai_api("Message response", delay=0.001)
        # Create a message.  The response will be streamed via SSE.
        request_kwargs = {
            "headers": {"Authorization": "Bearer " + verified_new_user["access_token"],
                        "X-Chat-ID": chat["id"]
                        },
            "json": {"content": f"Message {settings.chat_history_length-1}"}
        }
        # The first message will be sent and then the response will be streamed.
        for _ in stream_response("post","/chat/message/next",request_kwargs,client):
            pass
    # Check that the messages were passed into the openai API in ascending order
    # of chat_index.
    openai_create_kwargs = mock_openai_api.call_args.kwargs
    messages_contents = [message["content"] for message in openai_create_kwargs["messages"]]
    print('messages!')
    print(messages_contents)
    assert messages_contents == [f"Message {message_i}" for message_i in range(settings.chat_history_length)], "Check that the messages are in the correct order."

@describe(
""" Test that the message history is the correct length.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_history_correct_length(verified_new_user: dict, client: TestClient):
    # Create a chat
    chat = client.post("/chat",
                    headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                    json={}).json()
    # Enter >max_history messages into the chat
    for message_i in range(settings.chat_history_length+10):
        client.post("/chat/message",
                headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                        "X-Chat-ID": chat["id"]
                        },
                json={"content": f"Message {message_i}",
                      "role": "user"})
    with patch('openai.resources.chat.AsyncCompletions.create', new_callable=Mock) as mock_openai_api:
        mock_openai_api.side_effect = async_create_mock_streaming_openai_api("Message response", delay=0.001)
        # Create a message.  The response will be streamed via SSE.
        request_kwargs = {
            "headers": {"Authorization": "Bearer " + verified_new_user["access_token"],
                        "X-Chat-ID": chat["id"]
                        },
            "json": {"content": "Message 10"}
        }
        # The first message will be sent and then the response will be streamed.
        for _ in stream_response("post","/chat/message/next",request_kwargs,client):
            pass
    # Check that the messages were passed into the openai API in ascending order
    # of chat_index.
    openai_create_kwargs = mock_openai_api.call_args.kwargs
    messages_contents = [message["content"] for message in openai_create_kwargs["messages"]]
    assert len(messages_contents) == settings.chat_history_length, f'Chat history length is incorrect: {len(messages_contents)}.  Should be {settings.chat_history_length}.'

@describe(
""" Test stream interruption.

When a SSE stream is interrupted with a new "next message" request, that stream
is terminated and a new SSE stream is created that incorporates the new message.

Args:
    verified_new_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_stream_interruption(verified_new_user: dict, client: TestClient):
    # Create a chat
    chat = client.post("/chat",
                    headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                    json={})
    chat = chat.json()
    expected_response = "123456789012345678901234567890" # 3 seconds of streaming at 0.1 seconds per character.
    results_queue = Queue()
    # - Send a message with a long running response in a separate process.
    message_request_process = th.Thread(
         target = stream_patched_delayed_response,
         args = (expected_response, client, chat["id"], verified_new_user["access_token"], 0.1, results_queue)
    )
    message_request_process.start()
    # - Wait a short period of time, then post a new message to the database.
    # This message should be incorporated in the stream when we interrupt it.
    time.sleep(1)
    client.post("/chat/message",
            headers={"Authorization": "Bearer " + verified_new_user["access_token"],
                    "X-Chat-ID": chat["id"]
                    },
            json={"content": f"new message",
                    "role": "user"})
    # - Now send a new interruption message to the "next-message" endpoint.
    with patch('openai.resources.chat.AsyncCompletions.create', new_callable=Mock) as mock_openai_api:
        mock_openai_api.side_effect = async_create_mock_streaming_openai_api("Message 2 response", delay=0.001)
        # Create a message.  The response will be streamed via SSE.
        request_kwargs = {
            "headers": {"Authorization": "Bearer " + verified_new_user["access_token"],
                        "X-Chat-ID": chat["id"]
                        },
            "json": {"content": "Message 2"}
        }
        # The first message will be sent and then the response will be streamed.
        message_2_response = ''.join(stream_response("post","/chat/message/next",request_kwargs,client))
    # Check that the messages were passed into the openai API in ascending order
    # of chat_index.
    openai_create_kwargs = mock_openai_api.call_args.kwargs
    messages_contents = [message["content"] for message in openai_create_kwargs["messages"]]
    assert len(messages_contents) == 2, f'Chat length is incorrect: {len(messages_contents)}.  Should be {settings.chat_history_length}.'
    # - Wait for the thread to finish and then verify that it was interrupted.
    message_request_process.join()
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    assert ''.join(results) != expected_response, "Check that the first response was interrupted."
    # Verify that the second response was not interrupted.
    assert message_2_response == "Message 2 response", "Check that the second response was not interrupted."

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user, client):
    # First, create a chat for messages
    chat = client.post("/chat",
                       headers={"Authorization": "Bearer " + verified_new_user["access_token"],},
                       json={}).json()
    # Check the routes
    check_verified_route("post", "/chat/message/next", verified_new_user, client,
                         json={"content": "Hello, world! This is my first message in a chat."},
                         headers={"X-Chat-ID": chat["id"]})
