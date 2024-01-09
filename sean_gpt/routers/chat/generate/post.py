""" This module contains the route for generating chat completion stream tokens.
"""
import uuid
from typing import List
import json

from fastapi import APIRouter
from openai import AsyncOpenAI

from ....util.describe import describe
from ....database import RedisConnectionDep
from ....config import settings
from ....model.message import MessageCreate

openai_client = AsyncOpenAI(api_key = settings.openai_api_key)

router = APIRouter(prefix="/generate")

@describe(
""" Generates a chat completion stream token.

Args:
    messages (List[MessageCreate]):  The messages in the chat.
    current_user (AuthenticatedUser):  The user making the request.
    redis_conn (RedisConnectionDep):  The database session.

Returns:
    dict:  A stream token.
""")
@router.post("")
async def generate_stream_token(
    messages: List[MessageCreate],
    redis_conn: RedisConnectionDep):
    # Generate a stream token, a UUID, to store in the redis database as a key
    # for the stream, with the value being the list of messages.
    stream_token = str(uuid.uuid4())
    # Store the stream token in the redis database
    # Make sure to convert to a string.
    await redis_conn.set(stream_token, json.dumps([msg.model_dump() for msg in messages]))
    # Return the stream token
    return {"stream_token": stream_token}