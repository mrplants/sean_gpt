""" Tests for the /share_set endpoint. 
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

##############
# /share_set #
##############
# POST (protected, verified)
#   Create a new share set
#
# GET (protected, verified)
#   Get all share sets owned by the user, not including the "default share set" for each file.
#
# DELETE (protected, verified)
#   Delete a share set

from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe

from ..util.check_routes import check_verified_route

@describe(
""" Test that a share set can be created.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_create_share_set(client: TestClient, verified_new_user: dict):
    # Create a share set
    response = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # {
    #     "id": "..."
    #     "name": "test share set",
    #     "is_public": false,
    # }
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "test share set"
    assert response.json()["is_public"] == False

@describe(
""" Test that a share set can be retrieved.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_get_share_sets(client: TestClient, verified_new_user: dict):
    # First, create a share set
    share_set = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    ).json()
    # Get all share sets
    response = client.get(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # [
    #     {
    #         "id": "..."
    #         ...
    #     }
    # ]
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert response.json() == [share_set], "Could not retrieve share sets."

@describe(
""" Test that a share set can be deleted.

Args:
    client (TestClient): The test client.
    verified_new_user (dict): A verified new user.
""")
def test_delete_share_set(client: TestClient, verified_new_user: dict):
    # First, create a share set
    share_set = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    ).json()
    # Delete the share set
    response = client.delete(
        f"/share_set/{share_set['id']}",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
    )
    # The response should be:
    # HTTP/1.1 204 No Content
    assert response.status_code == 204, f"Expected 204 No Content, got {response.status_code}"

@describe(""" Test the verified and authorized routes. """)
def test_verified_and_authorized(verified_new_user, client):
    # Create a share set to use for testing
    share_set = client.post(
        "/share_set",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"name": "test share set"}
    ).json()
    check_verified_route("POST",
                           "/share_set",
                           body={"name": "test share set"},
                           verified_user=verified_new_user, client=client)
    check_verified_route("GET",
                            "/share_set",
                            verified_user=verified_new_user, client=client)
    check_verified_route("DELETE",
                           "/share_set",
                           body={"id": share_set["id"]},
                           verified_user=verified_new_user, client=client)
