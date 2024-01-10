""" This module contains the route for generating chat completion streams.
"""
import uuid

from fastapi import APIRouter

from ...util.describe import describe
from ...util.database import RedisConnectionDep
from ...config import settings
from ..user.util import IsVerifiedUserDep

router = APIRouter(prefix="/generate/chat")

@describe(
""" Create a chat completion token.

Args:
    current_user (AuthenticatedUser):  The user making the request.

Returns:
    dict: A dictionary containing the token.
""")
@router.get("/token", dependencies=[IsVerifiedUserDep])
async def generate_chat_response(
    redis_conn: RedisConnectionDep):
    # Create the token using uuid4
    token = str(uuid.uuid4())
    # Save the token in redis with a timeout
    await redis_conn.set(token, 1, ex=settings.app_chat_token_timeout_seconds)
    # Return the token
    return {"token": token}
