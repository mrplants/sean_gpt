""" Mock API Calls Router

This is for debugging purposes only.  It mocks external APIs.
"""
from fastapi import APIRouter

from . import twilio
from . import openai

router = APIRouter(
    tags=["Mock API Calls"],
)

router.include_router(twilio.router)
router.include_router(openai.router)

def startup():
    """ Startup logic for the mock router. """
    twilio.startup()
    openai.startup()

def shutdown():
    """ Shutdown logic for the mock router. """
    twilio.shutdown()
    openai.shutdown()
