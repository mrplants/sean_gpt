""" Twilio Messaging Router """
from fastapi import APIRouter, Depends

from .util import validate_twilio
from . import post

router = APIRouter(
    tags=["Twilio Messaging"],
    dependencies=[Depends(validate_twilio)]
)

router.include_router(post.router)
