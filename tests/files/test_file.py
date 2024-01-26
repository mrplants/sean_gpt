""" Tests for the /file endpoint. 
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

#########
# /file #
#########
# POST (protected, verified)
#   Upload a file for processing and metadata storage.
#
# GET (protected, verified)
#   Get a list of files accessible to the user (includes files shared with the user).
#   - The user can filter on:
#     -  Share Set ID (exact)
#     -  File ID
#     -  File Contents and Metadata (Semantic Search, default or user-set threshold)
#
# DELETE (protected, verified)
#   Delete a file.  The user must have own the file.
#
# /share_set
# GET (protected, verified)
#   Get a list of share sets that the file belongs to.
#
# /file/download
# GET (protected, verified)
#   Download a file.  The user must have access to the file.
#
# The SeanGPT Files API is designed to make a user's file contents searchable and available in their
# AI chats. It also provides a way to share searchable files with other users.  Here's how it works:
#
# 1. A user uploads a file to SeanGPT.
# 2. SeanGPT extracts the file metadata, indexes it, etc.
# 3. The file is now accessible to the user's AI assistant.
# -  The user can share the file with other users.  This simply makes the files metadata available
#    to the other user's AI assistant.
# -  The user can also create a "Share Set" which is a collection of files that can be shared with
#    other users.  Share Sets cannot contain other Share Sets.  A file can be in multiple Share
#    Sets.
# -  NOTE: Under the hood, it's really only Share Sets that can allow access to other users.  Every
#    file has a default share set that is created when the file is uploaded.  This default share set
#    is not visible to the user and cannot be deleted.  It only ever contains the file that it was
#    created for.
# -  Files cannot be edited once they are uploaded.
# -  The following file types are supported:
#    -  Text files (txt)
#    -  Markdown files (md)
#    -  Code files (py, js, html, css, etc.)
#    -  TODO: PDF files (pdf)
# TODO: Test for uploading large files
# TODO: Test that only file owners can access non-public files

from pathlib import Path
import threading as th

import httpx
from websockets.sync.client import connect as connect_ws
from websockets.exceptions import ConnectionClosed
import json

from sean_gpt.util.describe import describe
from sean_gpt.model.file import (
    SUPPORTED_FILE_TYPES,
    FILE_STATUS_COMPLETE,
    FILE_STATUS_PROCESSING,
    FILE_STATUS_AWAITING_PROCESSING)

from ..util.check_routes import check_verified_route

@describe(
""" Test that a file can be uploaded.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_upload(sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    # Create a temporary file
    temp_file = tmp_path / "temp.txt"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # {
    #     "id": "...",
    #     "owner_id": "...",
    #     "default_share_set_id": "...",
    #     "status": "...", # "awaiting processing", "processing", "complete"
    #     "name": "temp.txt",
    #     "type": "txt",
    #     "hash": "...",
    #     "uploaded_at": "...",
    #     "size": 13,
    # }
    assert upload_response.status_code == 200, (
        f"Expected status code 200. Received status code {upload_response.status_code}"
    )
    assert 'id' in upload_response.json(), (
        f"Expected response to contain 'id'. Received response {upload_response.json()}"
    )
    assert upload_response.json()['owner_id'] == verified_new_user['id'], (
        f"Expected response to contain 'owner_id'. Received response {upload_response.json()}"
    )
    assert 'default_share_set_id' in upload_response.json(), (
        f"Expected response to contain 'default_share_set_id'. "
        f"Received response {upload_response.json()}"
    )
    assert upload_response.json()['status'] in (FILE_STATUS_AWAITING_PROCESSING,
                                                FILE_STATUS_COMPLETE,
                                                FILE_STATUS_PROCESSING), (
        f"Expected response to contain 'status'. Received response {upload_response.json()}"
    )
    assert upload_response.json()['name'] == "temp.txt", (
        f"Expected response to contain 'name'. Received response {upload_response.json()}"
    )
    assert upload_response.json()['type'] == "txt", (
        f"Expected response to contain 'type'. Received response {upload_response.json()}"
    )
    assert 'hash' in upload_response.json(), (
        f"Expected response to contain 'hash'. Received response {upload_response.json()}"
    )
    assert 'uploaded_at' in upload_response.json(), (
        f"Expected response to contain 'uploaded_at'. Received response {upload_response.json()}"
    )
    assert upload_response.json()['size'] == 13, (
        f"Expected response to contain 'size'. Received response {upload_response.json()}"
    )

@describe(
""" Test that a file can be deleted.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_delete(sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    temp_file = tmp_path / "temp.txt"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    # Delete the file
    delete_response = httpx.delete(
        f"{sean_gpt_host}/file/{upload_response['id']}",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
    )
    # The response should be:
    # HTTP/1.1 204 No Content
    assert delete_response.status_code == 204, (
        f"Expected status code 204. Received status code {delete_response.status_code}, "
        f"response body: {delete_response.json()}"
    )

@describe(
""" Test that a file can be retrieved using the file ID.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_get_by_id(sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    temp_file = tmp_path.parent / "test_file.txt"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    # Retrieve the file
    get_response = httpx.get(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        params={"file_id": upload_response['id']}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # [{
    #     "id": "...",
    #  ...
    # }]
    assert get_response.status_code == 200, (
        f"Expected status code 200. Received status code {get_response.status_code}, "
        f"response body: {get_response.json()}"
    )
    assert get_response.json()[0]['id'] == upload_response['id'], (
        f"Expected response to contain 'id'. Received response {get_response.json()}"
    )

@describe(
""" Test that a file can be retrieved using the share set ID.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_get_by_share_set_id(sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    temp_file = tmp_path / "test_file.txt"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    # Retrieve the file
    get_response = httpx.get(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        params={"share_set_id": upload_response['default_share_set_id']}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # [{
    #     "id": "...",
    #  ...
    # }]
    assert get_response.status_code == 200, (
        f"Expected status code 200. Received status code {get_response.status_code}"
    )
    assert get_response.json()[0]['id'] == upload_response['id'], (
        f"Expected response to contain 'id'. Received response {get_response.json()}"
    )

@describe(
""" Test that a file can be retrieved using the file semantic search.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_get_by_semantic_search(sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    temp_file = tmp_path / "test_file.txt"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    # Wait for the file processing to be complete
    # Create a file processing token
    token = httpx.get(
        f"{sean_gpt_host}/file/processing/token",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"}).json()['token']
    timer = None
    # Connect to the websocket
    # Put in a try block to catch any disconnect exceptions
    try:
        with connect_ws(f"{sean_gpt_host}/file/processing/ws?token={token}".replace('http',
                                                                                    'ws')) as ws:
            # The first messagein the exchange is the prior: a list of messages.
            ws.send(json.dumps({
                'action': 'monitor_file_processing',
                'payload': {
                    'file_id': upload_response['id']
                }
            }))
            def timeout_assertion():
                ws.close()
                assert False, "The server took too long to respond."
            timer = th.Timer(30, timeout_assertion)
            timer.start()
            # The server will disconnect when the file is processed)
            print(f'Waiting for file processing to complete...')
            while True:
                print(f'Received message: {ws.recv()}')
    except ConnectionClosed:
        timer.cancel()

    # Retrieve the file
    get_response = httpx.get(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        params={
            "semantic_search": "Welcome, Globe!",
            "threshold": 0.5 # This is a very low threshold. Just for testing that it is accepted.
        }
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # [{
    #     "id": "...",
    #  ...
    # }]
    assert get_response.status_code == 200, (
        f"Expected status code 200. Received status code {get_response.status_code}"
    )
    assert get_response.json()[0]['id'] == upload_response['id'], (
        f"Expected response to contain 'id'. Received response {get_response.json()}"
    )

@describe(
""" Test that a only supported file types can be uploaded.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_upload_only_supported_types(
    sean_gpt_host: str,
    verified_new_user: dict,
    tmp_path: Path):
    # Loop over the supported types and check that each can be uploaded
    for file_type in SUPPORTED_FILE_TYPES:
        # Create a temporary file
        temp_file = tmp_path / f"test_file.{file_type}"
        temp_file.write_text("Hello, World!")
        upload_response = httpx.post(
            f"{sean_gpt_host}/file",
            headers={
                "Authorization": f"Bearer {verified_new_user['access_token']}"
            },
            files={"file": temp_file.open("rb")}
        )
        # The response should be:
        # HTTP/1.1 200 OK
        assert upload_response.status_code == 200, (
            f"Expected status code 200. Received status code {upload_response.status_code}"
        )
    # Hard to test for the negative, but just give it a shot with an ending that is not supported.
    # Create a temporary file
    temp_file = tmp_path / "test_file.not_supported"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    )
    # The response should be:
    # HTTP/1.1 422 Unprocessable Entity
    assert upload_response.status_code == 422, (
        f"Expected status code 422. Received status code {upload_response.status_code}"
    )

@describe(
""" Test that a file's share sets can be retrieved.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_get_share_sets(sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    # Create a temporary file
    temp_file = tmp_path / "temp.txt"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    # Retrieve the file's share sets
    get_response = httpx.get(
        f"{sean_gpt_host}/share_set",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        params={"file_id": upload_response['id']}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # [{
    #     "id": "...",
    #  ...
    # }]
    assert get_response.status_code == 200, (
        f"Expected status code 200. Received status code {get_response.status_code}"
    )
    assert get_response.json()[0]['id'] == upload_response['default_share_set_id'], (
        f"Expected response to contain 'id'. Received response {get_response.json()}"
    )

@describe(
""" Test that a file can be downloaded.

Args:
    sean_gpt_host (str): The host of the SeanGPT server.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary path.
""")
def test_file_download(sean_gpt_host: str, verified_new_user: dict, tmp_path: Path):
    # Create a temporary file
    temp_file = tmp_path / "temp.txt"
    temp_file.write_text("Hello, World!")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    # Download the file
    download_response = httpx.get(
        f"{sean_gpt_host}/file/download/{upload_response['id']}",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        }
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # "Hello, World!"
    assert download_response.status_code == 200, (
        f"Expected status code 200. Received status code {download_response.status_code}"
    )
    assert download_response.text == "Hello, World!", (
        f"Expected response to be 'Hello, World!'. Received response {download_response.text}"
    )

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user, sean_gpt_host, tmp_path):
    # Create and upload a file
    temp_file = tmp_path / "test.txt"
    temp_file.write_text("test file contents")
    check_verified_route("POST",
                         sean_gpt_host,
                            "/file",
                            files={"file": temp_file.open("rb")},
                            verified_user=verified_new_user)
    # Upload another file so that we have the ID for later checks
    temp_file = tmp_path / "test2.txt"
    temp_file.write_text("test file contents")
    upload_response = httpx.post(
        f"{sean_gpt_host}/file",
        headers={
            "Authorization": f"Bearer {verified_new_user['access_token']}"
        },
        files={"file": temp_file.open("rb")}
    ).json()
    check_verified_route("GET",
                         sean_gpt_host,
                            "/file",
                            params={"file_id": upload_response['id']},
                            verified_user=verified_new_user)
    check_verified_route("GET",
                         sean_gpt_host,
                            "/file",
                            params={"share_set_id": upload_response['default_share_set_id']},
                            verified_user=verified_new_user)
    check_verified_route("GET",
                         sean_gpt_host,
                            "/file",
                            params={"semantic_search": "test"},
                            verified_user=verified_new_user)
    check_verified_route("GET",
                         sean_gpt_host,
                            "/share_set",
                            params={"file_id": upload_response['id']},
                            verified_user=verified_new_user)
    check_verified_route("GET",
                         sean_gpt_host,
                            f"/file/download/{upload_response['id']}",
                            verified_user=verified_new_user)
    check_verified_route("DELETE",
                         sean_gpt_host,
                         f"/file/{upload_response['id']}",
                         verified_user=verified_new_user)
