
""" This module contains the route for generating chat completion streams.
"""
import json

from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from ....util.describe import describe
from ....database import RedisConnectionDep
from ....config import settings

openai_client = AsyncOpenAI(api_key = settings.openai_api_key)

router = APIRouter(prefix="/generate")

@describe(
""" Streams the assistant's response to a user message.

Args:
    user_message (Message):  The message to the assistant.
    x_chat_stream_token (str):  The stream token for the chat.
    current_user (AuthenticatedUser):  The user making the request.
    redis_conn (RedisConnectionDep):  The database session.

Yields:
    MessageChunk:  A chunk of the assistant's response.
""")
@router.get("")
async def generate_chat_response(
    *,
    x_chat_stream_token: str = Header(),
    redis_conn: RedisConnectionDep):
    print('connected')
    # Retrieve the messages from the redis database
    messages = json.loads(await redis_conn.get(x_chat_stream_token))

    # TODO: Incorporate different AI agents
    response_stream = await openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        stream=True,
    )

    async def iter_openai_stream():
        async for chunk in response_stream:
            if chunk.choices[0].delta.content is not None:
                yield f'data: {chunk.choices[0].delta.content}\n\n'
        yield 'data: \n\n'
        # Indicate that the assistant is no longer responding
    return StreamingResponse(iter_openai_stream(), media_type="text/event-stream")