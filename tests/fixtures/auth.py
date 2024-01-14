""" Test fixtures for user auth.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

from unittest.mock import Mock
import random

import pytest
import httpx

from sean_gpt.config import settings
from sean_gpt.util.describe import describe

@describe(""" Test fixture to provide an admin auth token. """)
@pytest.fixture
def admin_auth_token(sean_gpt_host: str) -> str:
    # Generate a token
    response = httpx.post(
        f"{sean_gpt_host}/user/token",
        data={
            "grant_type": "password",
            "username": settings.user_admin_phone,
            "password": settings.user_admin_password,
        },
    )
    return response.json()["access_token"]

@describe(""" Test fixture to provide an admin user. """)
@pytest.fixture
def admin_user(admin_auth_token: str, sean_gpt_host: str) -> dict:
    # Get the admin user
    response = httpx.get(
        f"{sean_gpt_host}/user",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json() | {"access_token": admin_auth_token}

@describe(""" Test fixture to provide a valid referral code. """)
@pytest.fixture
def referral_code(admin_auth_token: str, sean_gpt_host: str) -> str:
    # Get a referral code
    response = httpx.get(
        f"{sean_gpt_host}/user/referral_code",
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    return response.json()["referral_code"]

@describe(""" Test fixture to provide a new user and their auth token. """)
@pytest.fixture
def new_user(referral_code: str, sean_gpt_host: str) -> dict:
    # Create a new user with random phone and password
    new_user_phone = f"+{random.randint(10000000000, 20000000000)}"
    new_user_password = f"test{random.randint(0, 1000000)}"
    response_user = httpx.post(
        f"{sean_gpt_host}/user",
        json={
            "user": {
                "phone": new_user_phone,
                "password": new_user_password,
            },
            "referral_code": referral_code
        }
    )
    # Get the new user's auth token
    response_token = httpx.post(
        f"{sean_gpt_host}/user/token",
        data={
            "grant_type": "password",
            "username": new_user_phone,
            "password": new_user_password,
        },
    )
    yield response_user.json() | response_token.json() | {"password": new_user_password}
    # Delete the new user as cleanup
    httpx.delete(
        f"{sean_gpt_host}/user",
        headers={"Authorization": f"Bearer {response_token.json()['access_token']}"}
    )

@describe(""" Test fixture to provide a verified new user and their auth token. """)
@pytest.fixture
def verified_new_user(new_user: dict, sean_gpt_host: str) -> dict:
    # TODO: Re-enable this when Twilio campaign is ready
    # # Request new user verification code
    # client.post(
    #     "/user/request_phone_verification",
    #     headers={"Authorization": f"Bearer {new_user['access_token']}"}
    # )
    # # pylint: disable=no-member
    # code_message_regex = (settings.app_phone_verification_message
    #                       .format('(\\S+)')
    #                       .replace('.', '\\.'))
    # phone_verification_code = re.search(
    #     code_message_regex,
    #     mock_twilio_sms_create.call_args[1]["body"]
    # ).group(1)
    # # pylint enable=no-member
    # # Verify the user
    # client.put(
    #     "/user/is_phone_verified",
    #     headers={"Authorization": f"Bearer {new_user['access_token']}"},
    #     json={"phone_verification_code": phone_verification_code}
    # )
    yield new_user

@describe(""" Test fixture to provide a verified, opted-in user and their auth token. """)
@pytest.fixture
def verified_opted_in_user(
    verified_new_user: dict,
    sean_gpt_host: str) -> dict:
    opted_in_user = httpx.put(
        f"{sean_gpt_host}/user/opted_into_sms",
        headers={"Authorization": f"Bearer {verified_new_user['access_token']}"},
        json={"opted_into_sms": True}
    ).json()
    yield {**verified_new_user, **opted_in_user,}
