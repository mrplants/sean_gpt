################
# /users/token #
################
# POST (protected):  Login and retrieve a user's auth token

from fastapi.testclient import TestClient

from sean_gpt.config import settings
from sean_gpt.util.describe import describe

from .fixtures import *
from ..util import *

@describe(""" Test the verified and authorized routes. """)
def test_verified_authorized_routes(verified_new_user: dict, client: TestClient):
    check_authorized_route("POST", "/users/token", {
        "grant_type": "password",
        "username": verified_new_user["phone"],
        "password": verified_new_user["password"],
    }, authorized_user=verified_new_user, client=client)

@describe(""" Test that an authorization token can be generated. """)
def test_generate_token(client: TestClient):
    # Generate a token
    response = client.post(
        "/users/token",
        data={
            "grant_type": "password",
            "username": settings.admin_phone,
            "password": settings.admin_password,
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
    assert type(response.json()["access_token"]) == str

@describe(""" Test that an authorization token will expire. """)
def test_token_expiration(admin_auth_token: str, client: TestClient):
    # Check the expiration date of the token using JWT
    # The JWT expiration can be decoded and checked without the secret key.
    # Decode the token without verification
    unverified_claims = jwt.get_unverified_claims(admin_auth_token)
    assert unverified_claims["exp"] - unverified_claims["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    # Without waiting the full expiration time, it is not possible to write a
    # practical test for this.  Instead, we will perform a verified check
    # that the token will expire.
    decoded = jwt.decode(admin_auth_token, settings.secret_key, algorithms=[settings.algorithm])
    assert decoded["exp"] - decoded["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

@describe(""" Test that an authorization token will not be generated with an incorrect password. """)
def test_generate_token_incorrect_password(client: TestClient):
    # Generate a token
    response = client.post(
        "/users/token",
        data={
            "grant_type": "password",
            "username": settings.admin_phone,
            "password": "incorrect_password",
        },
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    # 
    # {"detail":"Unable to validate credentials"}
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"detail": "Incorrect username or password"}