""" Tests for the /share_set/* endpoints. 
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

##############
# /share_set/* #
##############
# /share_set/name
# PUT (protected, verified)
#   Update a share set name
#
# /share_set/file
# PUT (protected, verified)
#   Add a file to a share set
#
# /share_set/file
# DELETE (protected, verified)
#   Remove a file from a share set
#
# /share_set/is_public
# PUT (protected, verified)
#   Update a share set's public status
#
# TODO: Test that a share set can be shared more precisely than just public/private
# /share_set/users
# PUT (protected, verified)
#   Share this share set with a user (identified by phone number)
#
# /share_set/users
# DELETE (protected, verified)
#   Remove a user from a share set

from pathlib import Path

from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe

from ..util.check_routes import check_verified_route

@describe(
""" Test that a share set name can be updated.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_update_share_set_name(client: TestClient, verified_new_user: dict):
    # Create a share set
    response = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    )
    # Update the share set name
    response = client.put(
        "/share_set/name",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"id": response.json()["id"], "name": "test share set 2"}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # {
    #     "id": "..."
    #     "name": "test share set 2",
    #     "is_public": false,
    # }
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert "id" in response.json(), "Share set ID was not returned."
    assert response.json()["name"] == "test share set 2", "Share set name was not updated."
    assert not response.json()["is_public"], "Share set was made public."

@describe(
""" Test that a file can be added to a share set.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary directory.
""")
def test_add_file_to_share_set(client: TestClient, verified_new_user: dict, tmp_path: Path):
    # Create and upload a file
    temp_file = tmp_path / "test.txt"
    temp_file.write_text("test file contents")
    uploaded_file = client.post(
        "/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        files={"file": temp_file.open("rb")}
    ).json()
    # Create a share set
    share_set = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    ).json()
    # Add a file to the share set
    add_response = client.put(
        "/share_set/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"id": share_set["id"], "file_id": uploaded_file["id"]}
    )
    # The response should be:
    # HTTP/1.1 204 No Content
    assert add_response.status_code == 204, (
        f"Expected 204 No Content, got {add_response.status_code}")

    # Use the GET /file endpoint to check that the file was added
    get_response = client.get(
        "/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        params={"share_set_id": share_set['default_share_set_id']}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # [
    #     {
    #         "id": "..."
    #         ...
    #     }
    # ]
    assert get_response.status_code == 200, f"Expected 200 OK, got {get_response.status_code}"
    assert get_response.json() == [uploaded_file], "File was not added to share set."

@describe(
""" Test that a file can be removed from a share set.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
    tmp_path (Path): A temporary directory.
""")
def test_remove_file_from_share_set(client: TestClient, verified_new_user: dict, tmp_path: Path):
    # Create and upload a file
    temp_file = tmp_path / "test.txt"
    temp_file.write_text("test file contents")
    uploaded_file = client.post(
        "/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        files={"file": temp_file.open("rb")}
    ).json()
    # Create a share set
    share_set = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    ).json()
    # Add a file to the share set
    client.put(
        "/share_set/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"id": share_set["id"], "file_id": uploaded_file["id"]}
    )
    # Remove the file from the share set
    remove_response = client.delete(
        "/share_set/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"id": share_set["id"], "file_id": uploaded_file["id"]}
    )
    # The response should be
    # HTTP/1.1 204 No Content
    assert remove_response.status_code == 204, (
        f"Expected 204 No Content, got {remove_response.status_code}")

    # Use the GET /file endpoint to check that the file was removed
    get_response = client.get(
        "/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        params={"share_set_id": share_set['default_share_set_id']}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # []
    assert get_response.status_code == 200, f"Expected 200 OK, got {get_response.status_code}"
    assert get_response.json() == [], "File was not removed from share set."

@describe(
""" Test that a share set's public status can be updated.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_update_share_set_public_status(client: TestClient, verified_new_user: dict):
    # Create a share set
    share_set = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    ).json()
    # Update the share set's public status
    response = client.put(
        "/share_set/is_public",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"id": share_set["id"], "is_public": True}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # {
    #     "id": "..."
    #     ...
    #     "is_public": true,
    # }
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert response.json()["is_public"], "Share set was not made public."

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user, client, tmp_path):
    # Create and upload a file
    temp_file = tmp_path / "test.txt"
    temp_file.write_text("test file contents")
    uploaded_file = client.post(
        "/file",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        files={"file": temp_file.open("rb")}
    ).json()
    # Create a share set to use for testing
    share_set = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    ).json()
    check_verified_route("PUT",
                           "/share_set/name",
                           body={"name": "test share set"},
                           verified_user=verified_new_user, client=client)
    check_verified_route("PUT",
                            "/share_set/file",
                            body={"id": share_set["id"], "file_id": uploaded_file["id"]},
                            verified_user=verified_new_user, client=client)
    check_verified_route("DELETE",
                            "/share_set/file",
                            body={"id": share_set["id"], "file_id": uploaded_file["id"]},
                            verified_user=verified_new_user, client=client)
    check_verified_route("PUT",
                            "/share_set/is_public",
                            body={"id": share_set["id"], "is_public": True},
                            verified_user=verified_new_user, client=client)
