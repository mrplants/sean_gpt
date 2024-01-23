""" Tests for the /file/processing endpoint. 
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

####################
# /file/processing #
####################
#
# The /file/processing endpoint is used for realtime monitoring of file processing.  It uses
# websockets to stream updates to the client.  Each websocket stream can only be used for one file.
# The authentication happens similarly to the /generate/chat endpoint:
# - The client makes a GET request to /file/processing/token to get a token.
# - The client creates a websocket connection to /file/processing/ws?token=<token>.
# - The client sends the id of the file to monitor.
# - The server sends updates about the file processing.
# - When the file processing is complete, the server closes the connection.

from pathlib import Path
import json
import threading as th

import httpx
from websockets.sync.client import connect as connect_ws
from websockets.exceptions import ConnectionClosed

from sean_gpt.util.describe import describe
from sean_gpt.model.file import (
    FILE_STATUS_AWAITING_PROCESSING, FILE_STATUS_PROCESSING, FILE_STATUS_COMPLETE)

from ..util.check_routes import check_authorized_route

@describe(
""" Tests GET endpoint for file processing token generation.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_file_processing_token_get( # pylint: disable=missing-function-docstring
    sean_gpt_host: str, verified_new_user: dict):
    # Create a file processing token
    token_response = httpx.get(
        f"{sean_gpt_host}/file/processing/token",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"})
    # The response should be:
    # HTTP/1.1 200 OK
    # {
    #     "token": "..."
    # }
    assert token_response.status_code == 200, (
        f"Expected status code 200. Received status code {token_response.status_code}. "
        f"Response: {token_response.json()}"
    )
    assert 'token' in token_response.json(), (
        f"Expected response to contain 'token'. Received response {token_response.json()}."
    )

@describe(
""" Tests websocket endpoint for file processing.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path (pytest fixture).
""")
def test_file_processing_ws( # pylint: disable=missing-function-docstring
        sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    # Create a file to process
    temp_file = tmp_path / 'test_file.txt'
    temp_file.write_text('This is a test file.')
    # Upload the file
    file_record = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    # Create a file processing token
    token = httpx.get(
        f"{sean_gpt_host}/file/processing/token",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"}).json()['token']
    # Connect to the websocket
    # Put in a try block to catch any disconnect exceptions
    events = []
    timer = None
    try:
        with connect_ws(f"{sean_gpt_host}/file/processing/ws?token={token}".replace('http',
                                                                                    'ws')) as ws:
            # The first messagein the exchange is the prior: a list of messages.
            ws.send(json.dumps({
                'action': 'monitor_file_processing',
                'payload': {
                    'file_id': file_record['id']
                }
            }))
            # The server will disconnect when it is finished streaming.
            # Create a timer that will raise an exception if the server takes too long.
            def timeout_assertion():
                ws.close()
                assert False, "The server took too long to respond."
            timer = th.Timer(30, timeout_assertion)
            timer.start()
            while True:
                events.append(ws.recv())
            # All subsequent messages are the response.
    except ConnectionClosed:
        if timer:
            timer.cancel()
    # The order of events should be:
    # 1. FILE_STATUS_AWAITING_PROCESSING
    # 2. FILE_STATUS_PROCESSING
    # 3. FILE_STATUS_COMPLETE
    assert len(events) == 3, (
        f"Expected 3 events. Received {len(events)} events: {events}"
    )
    assert events == [
        FILE_STATUS_AWAITING_PROCESSING,
        FILE_STATUS_PROCESSING,
        FILE_STATUS_COMPLETE
    ]

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user: dict, sean_gpt_host:str): # pylint: disable=missing-function-docstring
    check_authorized_route("GET",
                           sean_gpt_host,
                           "/file/processing/token",
                           authorized_user=verified_new_user)
