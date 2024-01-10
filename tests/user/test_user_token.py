""" Tests for the user/token route.
"""

# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

###############
# /user/token #
###############
# POST (protected):  Login and retrieve a user's auth token

from fastapi.testclient import TestClient
from jose import jwt

from sean_gpt.config import settings
from sean_gpt.util.describe import describe

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(verified_new_user: dict, client: TestClient):
    # This endopint is not a verified or authorized route.
    pass

@describe(""" Test that an authorization token can be generated. """)
def test_generate_token(client: TestClient):
    # Generate a token
    response = client.post(
        "/user/token",
        data={
            "grant_type": "password",
            "username": settings.user_admin_phone,
            "password": settings.user_admin_password,
        },
    )
    # The response should be:
    # HTTP/1.1 200 OK
    # Content-Type: application/json
    #
    # {
    # "access_token": "...",
    # "token_type": "bearer"
    # }
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["token_type"] == "bearer"
    assert isinstance(response.json()["access_token"], str)

@describe(""" Test that an authorization token will expire. """)
def test_token_expiration(admin_auth_token: str, client: TestClient):
    # Check the expiration date of the token using JWT
    # The JWT expiration can be decoded and checked without the secret key.
    # Decode the token without verification
    unverified_claims = jwt.get_unverified_claims(admin_auth_token)
    assert (unverified_claims["exp"] - unverified_claims["iat"] ==
            settings.jwt_access_token_expire_minutes * 60)
    # Without waiting the full expiration time, it is not possible to write a
    # practical test for this.  Instead, we will perform a verified check
    # that the token will expire.
    decoded = jwt.decode(admin_auth_token,
                         settings.jwt_secret_key,
                         algorithms=[settings.jwt_algorithm])
    assert decoded["exp"] - decoded["iat"] == settings.jwt_access_token_expire_minutes * 60

@describe(""" Test that an authorization token will not be generated with an incorrect password """)
def test_generate_token_incorrect_password(client: TestClient):
    # Generate a token
    response = client.post(
        "/user/token",
        data={
            "grant_type": "password",
            "username": settings.user_admin_phone,
            "password": "incorrect_password",
        },
    )
    # The response should be:
    # HTTP/1.1 401 Unauthorized
    # Content-Type: application/json
    #
    # {
    # "detail": "Incorrect username or password"
    # }
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"detail": "Incorrect username or password"}
