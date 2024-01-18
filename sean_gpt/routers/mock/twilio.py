""" Mocks the twilio API for testing purposes.
"""
# Disable pylint flags for test fixtures:
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Disable pylint flags for new type of docstring:
# pylint: disable=missing-function-docstring

from unittest.mock import patch

from fastapi import APIRouter, Body
import redis

from ...config import settings

def get_valid(*_, **__):
    """ Mocks the twilio validator endpoint. """
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    valid = redis_conn.get("twilio_validator").decode("utf-8")
    return valid == "True"

def create_sms(to, body, *_, from_=None, **__):
    """ Mocks the twilio sms endpoint. """
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    redis_conn.set("latest_twilio_sms_body", body)
    redis_conn.set("latest_twilio_sms_from", from_)
    redis_conn.set("latest_twilio_sms_to", to)
    print('Mock SMS sent to', to, 'from', from_, 'with body', body)

# Apply patches in the global scope
validator_patch = patch('twilio.request_validator.RequestValidator.validate', new=get_valid)
create_sms_patch = patch('twilio.rest.api.v2010.account.message.MessageList.create', new=create_sms)

def startup():
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    redis_conn.set("twilio_validator", "True")
    redis_conn.set("latest_twilio_sms", "mocked sms from twilio")
    redis_conn.set("latest_twilio_sms_from", "+15555555555")
    redis_conn.set("latest_twilio_sms_to", "+15555555555")
    validator_patch.start()
    create_sms_patch.start()

def shutdown():
    validator_patch.stop()
    create_sms_patch.stop()

router = APIRouter(prefix="/mock/twilio")

@router.get("/sms")
def get_sms():
    """ Retrieves the most recently sent SMS."""
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    return {
        "body": redis_conn.get("latest_twilio_sms").decode("utf-8"),
        "from": redis_conn.get("latest_twilio_sms_from").decode("utf-8"),
        "to": redis_conn.get("latest_twilio_sms_to").decode("utf-8")
    }

@router.get("/validator")
def get_validator():
    """ Mock Twilio validator endpoint."""
    return {
        "valid": get_valid()
    }

@router.post("/validator")
def post_validator(*, valid: bool = Body(...)):
    """ Mock Twilio validator endpoint."""
    redis_conn = redis.from_url(f"redis://{settings.redis_host}")
    redis_conn.set("twilio_validator", str(valid))
