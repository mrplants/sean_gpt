########################
# /users/referral_code #
########################
# GET (protected, verified):  Get a user's referral code

from fastapi.testclient import TestClient

from sean_gpt.main import app
from sean_gpt.util.describe import describe

from .fixtures import *

client = TestClient(app)

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes():
    check_authorized_route("GET", "/users/referral_code")
    check_verified_route("GET", "/users/referral_code")

@describe(""" Test that a referral code can be generated. """)
def test_referral_code_generation(admin_user: dict):
    # Generate a referral code
    response = client.get(
        f"/users/referral_code",
        headers={"Authorization": f"Bearer {admin_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    #
    # {
    # "referral_code": "..."
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert type(response.json()["referral_code"]) == str

@describe(""" Test that a referral code cannot be generated for an unverified user. """)
def test_referral_code_generation_unverified(new_user: dict):
    # Generate a referral code
    response = client.get(
        f"/users/referral_code",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to generate referral code:  User phone is not verified."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to generate referral code:  User phone is not verified."
