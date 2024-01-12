""" Tests for user opt-in to SMS notifications. """
import random
from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe
from sean_gpt.config import settings

from ..util.check_routes import check_authorized_route
from ..util.sms import send_text, parse_twiml_msg

@describe(
""" Test that a user's SMS opt-in status can be set to True.
          
Args:
    new_user (dict): A new user created by the fixture.
    client (TestClient): A FastAPI test client.
""")
def test_sms_opt_in(new_user: dict, client: TestClient): # pylint: disable=missing-function-docstring
    # Change the user's opt-in status
    response = client.put(
        "/user/opted_into_sms",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={"opted_into_sms": True}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Body: the user's info
    assert response.status_code == 200
    assert response.json()["opted_into_sms"], f"User's phone was not verified: {response.json()}"

@describe(
""" Test that a user's SMS opt-in status can be set to False.
          
Args:
    new_user (dict): A new user created by the fixture.
    client (TestClient): A FastAPI test client.
""")
def test_sms_opt_out(new_user: dict, client: TestClient): # pylint: disable=missing-function-docstring
    # Change the user's opt-in status
    response = client.put(
        "/user/opted_into_sms",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={"opted_into_sms": False}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Body: the user's info
    assert response.status_code == 200
    assert not response.json()["opted_into_sms"], f"User phone was not verified: {response.json()}"

@describe(
""" Tests that an opted-out user receives only the opt-in request when they text the SMS endpoint.

Args:
    verified_new_user (dict): A verified new user.
    client (TestClient): A FastAPI test client.
""")
def test_sms_opt_out_sms( # pylint: disable=missing-function-docstring
    new_user: dict,
    client: TestClient):
    response = send_text(client,
                         from_number=new_user["phone"])
    # Instead of the simulated response, we should see the opt-in request
    # This is a twiml response, so we need to parse it
    assert parse_twiml_msg(response) == settings.app_sms_opt_in_message, (
        f"Expected opt-in request, got {parse_twiml_msg(response)}")

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes( # pylint: disable=missing-function-docstring
    verified_new_user: dict,
    client: TestClient):
    check_authorized_route("PUT", "/user/opted_into_sms", json={
        "opted_into_sms": True
    }, authorized_user=verified_new_user, client=client)
