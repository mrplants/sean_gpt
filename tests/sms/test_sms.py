""" Tests for the sms endpoint.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

########
# /sms #
########
# POST (Twilio-protected)
# - This is the twilio messagin webhook endpoint.  It only responds to
# twilio-verified requests.  It responds in twiml (https://www.twilio.com/docs/messaging/twiml)
#
# When a user interacts with this endpoint (sends a text to this service), even
# if the user has not been seen before, they are enrolled and automatically
# verified.  We give their account an invalid password hash so that they are
# forced to setup (i.e., reset) a password if they later choose to log into the
# service a different way.  Importantly, their account is marked as
# is_phone_verified=True because they must have a usable phone number if they
# are able to send a message to the Twilio messaging endpoint.
#
# For ease of use, this endopint sends async http requests to the other
# endpoints in the service.  While inefficient, it allows us to reuse the code
# at those endpoints as well as spread out the load a little in the kubernetes
# cluster.
#
# A user only has one Chat via their phone number.  It uses a reserved chat name
# that is setup when they create an account.
# TODO Missing Tests
# - Test that the openai message break character works "|"
# - Test that the welcome message includes a contact card for the AI (or link to one)
from unittest.mock import patch, Mock
import xml.etree.ElementTree as ET
import random
import threading as th
import time

import httpx
from sqlmodel import Session, select

from sean_gpt.util.describe import describe
from sean_gpt.config import settings
from sean_gpt.util.database import get_db_engine
from sean_gpt.model.authenticated_user import AuthenticatedUser

from ..util.sms import send_text, parse_twiml_msg
from ..util.mock import patch_openai_async_completions

@describe(
""" Tests that only Twilio-validated messages receive a valid response.

Args:
    client (TestClient):  A test client.
""")
def test_twilio_validated(sean_gpt_host: str):
    response = send_text(sean_gpt_host)
    assert response.status_code == 200, (
        f"Expected status code 200 for valid Twilio request, got {response.status_code}. "
        "Response: {response.content}"
    )
    response = send_text(sean_gpt_host, valid=False)
    assert response.status_code != 200, (
        "Expected status code other than 200 for invalid Twilio request, "
        f"got {response.status_code}, response: {response.content}")

@describe(
""" Tests that chat messages are saved.

Both the incoming message and each response message must be saved to the Chat in
the database.  Note that there must be at least one chat in the user's twilio
chat, otherwise the user will receive the welcome message (first message is ignored).

Args:
    verified_opted_in_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_messages_saved(verified_opted_in_user: dict, sean_gpt_host: str):
    # Create a message in the Twilio chat
    httpx.post(f"{sean_gpt_host}/chat/message",
        headers={
            "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
            "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
        },
        json={
            "role": "user",
            "content": "This is an initial message."
        })
    incoming_msg = "This is a test incoming user message."
    outgoing_msg = "This is a test outgoing assistant response message."
    send_text(sean_gpt_host,
              body=incoming_msg,
              openai_response=outgoing_msg,
              from_number=verified_opted_in_user["phone"])
    # Retrieve the messages in the twilio chat
    # The message endpoint retrieve messages one-by-one. You can query the message index with query
    # param 'chat_index', with zero being the oldest message.
    saved_messages = []
    for chat_index in range(3):
        saved_messages.append(httpx.get(
            f"{sean_gpt_host}/chat/message",
            headers={
                "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
                "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
            },
            params={"chat_index": chat_index}).json())
    # Check that the first message is the incoming message
    assert saved_messages[1]['role'] == 'user', (
        f"Expected first message to have role='user', got {saved_messages[0]['role']}"
    )
    assert saved_messages[1]['content'] == incoming_msg, (
        f"Expected first message to be '{incoming_msg}', got {saved_messages[0]['content']}"
    )
    # Check that the second message is the outgoing message
    assert saved_messages[2]['role'] == 'assistant', (
        f"Expected second message to have role='assistant', got {saved_messages[1]['role']}"
    )
    assert saved_messages[2]['content'] == outgoing_msg, (
        f"Expected second message to be '{outgoing_msg}', got {saved_messages[1]['content']}"
    )
    # check that only two messages exist
    assert len(saved_messages) == 3, f"Expected only three messages, got {len(saved_messages)}"

@describe(
""" Tests that all multi-messages contain a redirect and multi-part indication.

Messages in a multi-message response must contain a text indication that there
will be multiple messages.  Multi-message responses are generated when the
assistant has greater than 160 characters to respond with.

Args:
    verified_opted_in_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_multi_message(verified_opted_in_user: dict, sean_gpt_host: str):
    # Create a message in the Twilio chat so that we don't get the welcome
    # message.
    httpx.post(f"{sean_gpt_host}/chat/message",
        headers={
            "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
            "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
        },
        json={
            "role": "user",
            "content": "This is an initial message."
        })
    # The response message must be greater X charactere to trigger a
    # multi-message response.  Make a message that is X+1 characters long.
    outgoing_msg = ''.join(['a' for _ in range(settings.app_max_sms_characters+1)])
    # When this occurs, an ellipsis emoji is appended to the end of the message.
    # This takes only one character.
    response = send_text(sean_gpt_host,
                         openai_response=outgoing_msg,
                         from_number=verified_opted_in_user["phone"])
    # Parse the XML response
    root = ET.fromstring(response.content)

    # Check that the root element is 'Response'
    assert root.tag == 'Response', f"Expected root element to be 'Response', got {root.tag}"

    # Check that the first child element is 'Message'
    assert root[0].tag == 'Message', (
        f"Expected first child element to be 'Message', got {root[0].tag}")

    # Check that the text of the 'Message' element is the outgoing message
    # Note that it should be only the first X characters of the outgoing
    # message with the ellipsis emoji appended.
    expected_message = outgoing_msg[:settings.app_max_sms_characters-1] + '…'
    assert root[0].text == expected_message, (
        f"Expected first child element text to be '{expected_message}', got {root[0].text}")

    # Check that the second child element is 'Redirect'
    assert root[1].tag == 'Redirect', (
        f"Expected second child element to be 'Redirect', got {root[1].tag}")

    # Check that the text of the 'Redirect' element is the SMS endpoint
    assert root[1].text == './', (
        f"Expected second child element text to be './', got {root[1].text}")

    # Check that there are no more child elements
    assert len(root) == 2, f"Expected only two child elements, got {len(root)}"

@describe(
""" Tests that a previously created user gets their phone verified.

If a user has already been created, they should be able to send a message to
this endpoint and have their account marked as phone verified.

Args:
    new_user (dict):  An unverified user.
    client (TestClient):  A test client.
""")
def test_phone_verified(new_user: dict, sean_gpt_host: str):
    send_text(client, from_number=new_user["phone"])
    # Retrieve the user
    user = httpx.get(f"{sean_gpt_host}/user",
        headers={
            "Authorization": f"Bearer {new_user['access_token']}"
        }).json()
    # Check that the user is phone verified
    assert user["is_phone_verified"], (
        f"Expected user to be phone verified, got {user['is_phone_verified']}")

@describe(
""" Tests that an account is created for new users with valid referral codes.

A user's account is created when they message the endpoint for the first time,
as long as they have a valid referral code.

Args:
    client (TestClient):  A test client.
""")
def test_account_created(referral_code:str, sean_gpt_host: str):
    # Create a new user with a valid referral code
    # Pick a random US phone number to match against the User
    random_phone_number = f"+{random.randint(10000000000, 20000000000)}"
    response = send_text(sean_gpt_host,
                         from_number=random_phone_number,
                         body=referral_code)
    # Next the user will be prompted to opt-in
    # Check that the text of the 'Message' element is the opt-in message
    assert parse_twiml_msg(response) == settings.app_sms_opt_in_message, (
        f"Expected message response to be '{settings.app_sms_opt_in_message}', "
        f"got {parse_twiml_msg(response)}")
    # Have the user opt-in by sending "AGREE" to the endpoint
    response = send_text(sean_gpt_host,
                        from_number=random_phone_number,
                        body="AGREE")

    # Instead of the simulated response, we should see the welcome message
    # This is a twiml response, so we need to parse it
    # Check that the text of the 'Message' element is the welcome message
    assert parse_twiml_msg(response) == settings.app_welcome_message, (
        f"Expected message response to be '{settings.app_welcome_message}', "
        f"got {parse_twiml_msg(response)}")
    # Now we need to check that the database has the new user
    # We cannot do this via the endpoint because the user has no credentials yet
    # Instead, we will check the database directly
    # Retrieve the user
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        user = (session
                .exec(select(AuthenticatedUser)
                      .where(AuthenticatedUser.phone == random_phone_number))
                .first())
    assert user is not None, 'User not created after valid referral.'
    assert user.is_phone_verified, 'User should be phone verified.'
    assert user.hashed_password == "", 'User should have no password hash.'

@describe(
""" Tests that an account is not created for new users without a valid referral.

The endpoint will respond with static messages (requesting the referral code)
until the user sends a text with only the referral code.

Args:
    client (TestClient): A test client.
""")
def test_account_not_created(sean_gpt_host: str):
    random_phone_number = f"+{random.randint(10000000000, 20000000000)}"
    response = send_text(client,
                         from_number=random_phone_number,
                         body='user does not have a referral code')
    # Check that the text of the 'Message' element is the referral message
    assert parse_twiml_msg(response) == settings.app_request_referral_message, (
        f"Expected message response to be '{settings.app_request_referral_message}', "
        "got {parse_twiml_msg(response)}")
    # Retrieve the user
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        user = session.exec(select(AuthenticatedUser)
                            .where(AuthenticatedUser.phone == random_phone_number)).first()
    assert user is None, 'User created after invalid referral.'

@describe(
""" Tests that the correct system message is sent to the openai endpoint.

Args:
    verified_opted_in_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_system_message(verified_opted_in_user: dict, sean_gpt_host: str):
    # Create a message in the Twilio chat
    httpx.post(f"{sean_gpt_host}/chat/message",
        headers={
            "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
            "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
        },
        json={
            "role": "user",
            "content": "This is an initial message."
        })
    # Send a text to the endpoint
    # Use our own patch for the openai endpoint so we can retrieve the system message
    with patch_openai_async_completions(sean_gpt_host,
                                        "assistant message response",
                                        delay=0.001) as retrieve_call_args:
        send_text(sean_gpt_host,
                  from_number=verified_opted_in_user["phone"],
                  patch_openai_api=False)
        # Check that the correct system message was sent to the openai endpoint
        # The first message is the system message.
        # Check that it has role=system and content=settings.twilio_system_message
        system_message = retrieve_call_args()['kwargs']['messages'][0]
        assert system_message['role'] == 'system', (
            f"Expected system message to have role='system', got {system_message['role']}")
        assert system_message['content'] == settings.app_ai_system_message, (
            f"Expected system message to be the system message, got {system_message['content']}")

@describe(
""" Tests that interrupted multi-message responses stop sending messages.

When a user sends a message to the Twilio messaging endpoint, they will receive
a multi-message (message + redirect) response if the assistant has more than 160
characters to respond with.  If the user sends another message before the
assistant has finished responding, the assistant should stop sending messages.

Args:
    verified_opted_in_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_interrupted_multi_message(verified_opted_in_user: dict, sean_gpt_host: str):
    # Create a message in the Twilio chat
    httpx.post(f"{sean_gpt_host}/chat/message",
        headers={
            "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
            "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
        },
        json={
            "role": "user",
            "content": "First message to ignore welcome message."
        })
    # The response message must be greater 160 charactere to trigger a
    # multi-message response.  Make a message that is 161 characters long.
    outgoing_msg = ''.join(['a' for _ in range(161)])
    # When this occurs, an ellipsis emoji is appended to the end of the message.
    # This takes only one character.
    first_message_thread = th.Thread(
        target = send_text,
        args = (sean_gpt_host,),
        kwargs = {
            "body": "This is an initial message.",
            "openai_response": outgoing_msg,
            "from_number": verified_opted_in_user["phone"],
            "delay": 0.2 # About 3 seconds to respond, long enough to interrupt
        })
    first_message_thread.start()
    # - Wait a short period of time
    time.sleep(1)
    # - Now send a new interruption message.  This one doesn't ahve to be asynchronous.
    send_text(sean_gpt_host,
              body="This is an interruption message.",
              openai_response= "This is the response to the interruption message.",
              from_number=verified_opted_in_user["phone"])
    first_message_thread.join()
    # Check that the user's twilio chat has three messages:
    # - The first message from the user
    # - The interruption message from the user
    # - The interruption response from the assistant
    twilio_chat_messages = []
    len_twilio_chat_messages = httpx.get(
        f"{sean_gpt_host}/chat/message/len",
        headers={
            "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
            "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
        }).json()['len']
    for chat_index in range(len_twilio_chat_messages):
        twilio_chat_messages.append(httpx.get(
            f"{sean_gpt_host}/chat/message",
            headers={
                "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
                "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
            },
            params={"chat_index": chat_index}).json())
    assert len(twilio_chat_messages) == 4, (
        f"Expected only four messages, got {len(twilio_chat_messages)}")
    assert twilio_chat_messages[0]['role'] == 'user', (
        f"Expected first message to have role='user', got {twilio_chat_messages[0]['role']}")
    assert twilio_chat_messages[0]['content'] == "First message to ignore welcome message.", (
        f"Expected first message to be 'First message to ignore welcome message.', "
        f"got {twilio_chat_messages[0]['content']}")
    assert twilio_chat_messages[1]['role'] == 'user', (
        f"Expected second message to have role='user', got {twilio_chat_messages[1]['role']}")
    assert twilio_chat_messages[1]['content'] == "This is an initial message.", (
        f"Expected second message to be 'This is an initial message.', "
        f"got {twilio_chat_messages[1]['content']}")
    assert twilio_chat_messages[2]['role'] == 'user', (
        f"Expected second message to have role='user', got {twilio_chat_messages[1]['role']}")
    assert twilio_chat_messages[2]['content'] == "This is an interruption message.", (
        f"Expected second message to be 'This is an interruption message.', "
        f"got {twilio_chat_messages[1]['content']}")
    assert twilio_chat_messages[3]['role'] == 'assistant', (
        f"Expected third message to have role='assistant', got {twilio_chat_messages[2]['role']}")
    assert (twilio_chat_messages[3]['content'] ==
            "This is the response to the interruption message."), (
                f"Expected third message to be 'This is the response to the interruption message.',"
                f" got {twilio_chat_messages[2]['content']}")

@describe(
""" Tests that only SMS is supported.

Args:
    verified_opted_in_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_only_sms(verified_opted_in_user: dict, sean_gpt_host: str):
    # Send a text to the endpoint (whatsapp)
    response = send_text(sean_gpt_host,
                         from_number=f'whatsapp:{verified_opted_in_user["phone"]}',
                         body="This is a test message.")
    # The response should be a valid twiml message saying that only SMS is
    # supported.
    assert parse_twiml_msg(response) == settings.app_no_whatsapp_message, (
        f"Expected message response to be '{settings.app_no_whatsapp_message}', "
        f"got {parse_twiml_msg(response)}")
    # Send a text to the endpoint (MMS)
    response = send_text(sean_gpt_host,
                         from_number=verified_opted_in_user["phone"],
                         body="This is a test message.",
                         num_media=1)
    # The response should be a valid twiml message saying that only SMS is
    # supported.
    assert parse_twiml_msg(response) == settings.app_no_mms_message, (
        f"Expected message response to be '{settings.app_no_mms_message}', "
        f"got {parse_twiml_msg(response)}")

@describe(
""" Tests that the follow-on messages work.

A followon message is defined as the same request sent twice (same message SID)
A followon message must start with an ellipsis.
A middle message in a 3-message series must start and end with an ellipsis,
since it has a redirect.
Any message with a redirect must end with an ellipsis.

Args:
    verified_opted_in_user (dict):  A verified user.
    client (TestClient):  A test client.
""")
def test_followon_messages(verified_opted_in_user: dict, sean_gpt_host: str):
    # Start by posting a message to the twilio_chat so that we don't get the
    # welcome message.
    httpx.post(f"{sean_gpt_host}/chat/message",
        headers={
            "Authorization": f"Bearer {verified_opted_in_user['access_token']}",
            "X-Chat-ID": verified_opted_in_user["twilio_chat_id"]
        },
        json={
            "role": "user",
            "content": "This is an initial message."
        })
    # None of this needs to be asynchronous.
    # This test will act like a properly functioning twilio client.
    # When it receives a redirect, it will follow it (only "./" is supported).
    # First, list the assistant messages.  All but the last should be longer
    # than max characters to trigger a redirect.
    assistant_responses = [
        'a'*(settings.app_max_sms_characters + 1),
        'b'*(settings.app_max_sms_characters + 1),
        'c'*(settings.app_max_sms_characters + 1),
        'd'*(settings.app_max_sms_characters + 1),
        "This is the last message.",
    ]
    # Since this is a redirect, all messages must have the same message_sid
    message_sid = 'SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    for msg_index, assistant_response in enumerate(assistant_responses):
        response = send_text(sean_gpt_host,
                             openai_response=assistant_response,
                             from_number=verified_opted_in_user["phone"],
                             message_sid=message_sid)
        response_msg = parse_twiml_msg(response)
        # For the first message, check that it ends with an ellipsis but does not start with one
        if msg_index == 0:
            assert response_msg.endswith('…'), (
                f"Expected message response to end with '…', got {response_msg}")
            assert not response_msg.startswith('…'), (
                f"Expected message response to not start with '…', got {response_msg}")
        # For the middle messages, check that it starts and ends with an ellipsis
        elif msg_index < len(assistant_responses) - 1:
            assert response_msg.startswith('…'), (
                f"Expected message response to start with '…', got {response_msg}")
            assert response_msg.endswith('…'), (
                f"Expected message response to end with '…', got {response_msg}")
        # For the last message, check that it starts with, but does not end with an ellipsis
        else:
            assert response_msg.startswith('…'), (
                f"Expected message response to start with '…', got {response_msg}")
            assert not response_msg.endswith('…'), (
                f"Expected message response to not end with '…', got {response_msg}")
        # Only check for redirects if this is not the last message
        if msg_index < len(assistant_responses) - 1:
            # Parse the XML response
            root = ET.fromstring(response.content)
            # Check that the second child element is 'Redirect'
            assert root[1].tag == 'Redirect', (
                f"Expected second child element to be 'Redirect', got {root[1].tag}")
            # Check that the text of the 'Redirect' element is the SMS endpoint
            assert root[1].text == './', (
                f"Expected second child element text to be './', got {root[1].text}")
            # Check that there are no more child elements
            assert len(root) == 2, f"Expected only two child elements, got {len(root)}"
