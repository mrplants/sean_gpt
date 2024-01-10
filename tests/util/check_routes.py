""" Utility functions for checking authorized or verified routes.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

import random

from fastapi.testclient import TestClient

from sean_gpt.util.describe import describe

@describe(""" Checks that a route requires authorization for access. """)
def check_authorized_route(
    request_type: str,
    route: str,
    authorized_user: dict,
    client: TestClient,
    **request_kwargs):
    request_func = {
        "get": client.get,
        "post": client.post,
        "put": client.put,
        "delete": client.delete
    }[request_type.lower()]
    headers = {
        "Authorization": f"Bearer {authorized_user['access_token']}"
    } | request_kwargs.get("headers", {})
    response = request_func(
        route,
        headers=headers,
        **{k: v for k, v in request_kwargs.items() if k != 'headers'}
    )
    # The response should be any 2xx response code
    assert response.status_code // 100 == 2, (
        f"Expected status code 2xx, got {response.status_code}."
        "Response body: {response.content}"
    )
    # Now send an unauthorized request
    headers = {"Authorization": "Bearer invalid_token"} | request_kwargs.get("headers", {})
    response = client.post(
        route,
        headers=headers,
        **{k: v for k, v in request_kwargs.items() if k != 'headers'}
    )
    # The response should not be a 2xx response code
    assert response.status_code // 100 != 2, (
        f"Expected status code NOT 2xx, got {response.status_code}."
        "Response body: {response.content}"
    )

@describe(""" Checks that a route requires a verified user for access. """)
def check_verified_route(
    request_type: str,
    route: str,
    verified_user: dict,
    client: TestClient,
    **request_kwargs):
    # First, create an unverified user from the referral code of the verified user
    new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    new_user_password = f"test{random.randint(0, 1000000)}"
    unverified_user = client.post(
        "/user",
        json={
            "user": {
                "phone": new_user_phone,
                "password": new_user_password,
            },
            "referral_code": verified_user['referral_code']
        }
    ).json()
    # Get the new user's auth token
    unverified_user = unverified_user | client.post(
        "/user/token",
        data={
            "grant_type": "password",
            "username": new_user_phone,
            "password": new_user_password,
        },
    ).json() | {"password": new_user_password}

    request_func = {
        "get": client.get,
        "post": client.post,
        "put": client.put,
        "delete": client.delete
    }[request_type.lower()]
    headers = {
        "Authorization": f"Bearer {verified_user['access_token']}"
    } | request_kwargs.get("headers", {})
    response = request_func(
        route,
        headers=headers,
        **{k: v for k, v in request_kwargs.items() if k != 'headers'}
    )
    # The response should be any 2xx response code
    assert response.status_code // 100 == 2, (
        f"Expected status code 2xx, got {response.status_code}. "
        "Response body: {response.text}"
    )
    # Now send an unverified request
    headers = {
        "Authorization": f"Bearer {unverified_user['access_token']}"
    } | request_kwargs.get("headers", {})
    response = request_func(
        route,
        headers=headers,
        **{k: v for k, v in request_kwargs.items() if k != 'headers'}
    )
    # The response should not be a 2xx response code
    assert response.status_code // 100 != 2, (
        f"Expected status code NOT 2xx, got {response.status_code}. "
        "Response body: {response.text}"
    )
