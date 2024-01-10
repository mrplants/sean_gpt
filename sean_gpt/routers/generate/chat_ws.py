""" This module contains the route for generating chat completion via websocket.
"""
from fastapi import APIRouter, WebSocket, status, WebSocketException, WebSocketDisconnect, Query
from openai import AsyncOpenAI

from ...util.describe import describe
from ...config import settings
from ...util.database import RedisConnectionDep

openai_client = AsyncOpenAI(api_key = settings.openai_api_key)

router = APIRouter(prefix="/generate/chat")

@describe(
""" Generates a chat completion stream via websocket.

Args:
    current_user (AuthenticatedUser):  The user making the request.
""")
@router.websocket("/ws")
async def generate_chat_stream(
    *,
    token: str = Query(),
    redis_conn: RedisConnectionDep,
    websocket: WebSocket):
    # First, check that the token is valid in redis
    if not await redis_conn.exists(token):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    # Delete the token from redis
    await redis_conn.delete(token)
    # Accept the connection
    await websocket.accept()
    # Read the first message, which is:
    #  {
    #      'action': 'chat_completion',
    #      'payload': {
    #          'conversation': [
    #              {
    #                  "role": "...",
    #                  "content": "..."
    #              },
    #              ...
    #          ]
    #      }
    #  }
    # Put the websocket in a try block to catch any disconnect exceptions
    try:
        message = await websocket.receive_json()
        if message['action'] != 'chat_completion':
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        if 'conversation' not in message['payload']:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        # Get the conversation
        conversation = message['payload']['conversation']
        # Send the request to OpenAI
        # TODO: Incorporate different AI agents
        response_stream = await openai_client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=conversation,
            stream=True,
        )
        # Send the response back to the client chunk by chunk
        async for chunk in response_stream:
            if chunk.choices[0].delta.content is not None and chunk.choices[0].delta.content != '':
                await websocket.send_text(chunk.choices[0].delta.content)
        await websocket.close()
    except WebSocketDisconnect:
        # The client disconnected, so close the websocket
        await websocket.close()
