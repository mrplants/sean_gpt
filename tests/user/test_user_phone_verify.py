""" Tests for the /user/request_phone_verification route.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=no-member

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

####################################
# /user/request_phone_verification #
####################################
# POST (protected):  Request a phone verification code sent to the user's phone

############################
# /user/is_phone_verified #
############################
# PUT (protected):  Verify a user's phone

import httpx

from sean_gpt.util.describe import describe
from sean_gpt.config import settings

# from ..util.check_routes import check_authorized_route

# TODO: Re-enable this when Twilio campaign is ready
# @describe(""" Test the verified and authorized routes. """)
# def test_verified_authorized_routes(new_user: dict,
#                                     sean_gpt_host: str):
#     check_authorized_route("POST",
#                            "/user/request_phone_verification",
#                            authorized_user=new_user,
#                            client=client)
#     verification_msg = mock_twilio_sms_create.call_args[1]["body"]
#     code_message_regex = (settings.app_phone_verification_message
#                           .format('(\\S+)')
#                           .replace('.', '\\.'))
#     phone_verification_code = re.search(code_message_regex, verification_msg).group(1)
#     check_authorized_route("PUT", "/user/is_phone_verified", json={
#         "phone_verification_code": phone_verification_code
#     }, authorized_user=new_user, client=client)

# TODO: Re-enable this when Twilio campaign is ready
# @describe(""" Test that a user's phone can be verified.

# A user's phone is verified with this flow:
# - User requests a verification code.
# - Verification code is sent to the user's phone.
# - User submits the verification code.

# Here, we will mock the twilio client to return a known verification code.
# """)
# def test_phone_verification(new_user: dict, sean_gpt_host: str):
#     # Request new user verification code
#     client.post(
#         "/user/request_phone_verification",
#         headers={"Authorization": f"Bearer {new_user['access_token']}"}
#     )
#     verification_msg = mock_twilio_sms_create.call_args[1]["body"]
#     code_message_regex = (settings.app_phone_verification_message
#                           .format('(\\S+)')
#                           .replace('.', '\\.'))
#     phone_verification_code = re.search(code_message_regex, verification_msg).group(1)
#     # Check that the verification code message is properly formatted
#     assert (verification_msg ==
#             settings.app_phone_verification_message.format(phone_verification_code))
#     # Pass the user's verification code to update the phone verification status
#     response = client.put(
#         "/user/is_phone_verified",
#         headers={"Authorization": f"Bearer {new_user['access_token']}"},
#         json={"phone_verification_code": phone_verification_code}
#     )
#     # The response should be:
#     # HTTP/1.1 204 No Content
#     assert response.status_code == 204
#     # Check that the user's phone is verified
#     response = client.get(
#         "/user",
#         headers={"Authorization": f"Bearer {new_user['access_token']}"}
#     )
#     assert response.json()["is_phone_verified"]

@describe(""" Test that a user's phone cannot be verified with an incorrect verification code. """)
def test_phone_verification_incorrect_code(new_user: dict,
                                           sean_gpt_host: str):
    # Attempt to verify a user with no verification code
    response = httpx.put(
        f"{sean_gpt_host}/user/is_phone_verified",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={"phone_verification_code": "incorrect_code"}
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to verify phone:  Invalid verification code."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to verify phone:  Invalid verification code."
    # Request a verification code, then attempt with an incorrect verification code
    httpx.post(
        f"{sean_gpt_host}/user/request_phone_verification",
        headers={"Authorization": f"Bearer {new_user['access_token']}"}
    )
    response = httpx.put(
        f"{sean_gpt_host}/user/is_phone_verified",
        headers={"Authorization": f"Bearer {new_user['access_token']}"},
        json={"phone_verification_code": "incorrect_code"}
    )
    # The response should be:
    # HTTP/1.1 400 Bad Request
    # Content-Type: application/json
    #
    # {
    # "detail": "Unable to verify phone:  Invalid verification code."
    # }
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.json()["detail"] == "Unable to verify phone:  Invalid verification code."
