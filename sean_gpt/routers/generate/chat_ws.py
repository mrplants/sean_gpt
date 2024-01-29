""" This module contains the route for generating chat completion via websocket.
"""
from fastapi import APIRouter, WebSocket, status, WebSocketException, WebSocketDisconnect, Query
from openai import AsyncOpenAI

from sean_gpt.ai import default_ai

from ...util.describe import describe
from ...config import settings
from ...util.database import RedisConnectionDep
from ...ai import default_ai, nuclear_tools, run_tool

openai_client = AsyncOpenAI(api_key = settings.openai_api_key)

router = APIRouter(prefix="/generate/chat")

@describe(
""" Generates a chat completion stream via websocket.

Args:
    current_user (AuthenticatedUser):  The user making the request.
""")
@router.websocket("/ws")
async def generate_chat_stream( # pylint: disable=missing-function-docstring
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
        include_tools = True
        while response_stream := await get_chat_completion_stream(conversation, include_tools):
            # Send the response back to the client chunk by chunk
            finish_reason = None
            async for chunk in response_stream:
                if chunk.choices[0].delta.content is not None and chunk.choices[0].delta.content != '':
                    await websocket.send_text(chunk.choices[0].delta.content)
                if chunk.choices[0].delta.tool_calls is not None:
                    tool_call_results = []
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        if not tool_call.function or not tool_call.function.name or not tool_call.function.arguments:
                            continue
                        tool_call_results.append(run_tool(tool_call.function.name, tool_call.function.arguments))
                    for result in tool_call_results:
                        conversation.append({
                            "role": "assistant",
                            "content": result
                        })
                finish_reason = chunk.choices[0].finish_reason
            if finish_reason is not None and finish_reason != "tool_calls":
                break
            # Only send the tools once
            include_tools = False
        await websocket.close()
    except WebSocketDisconnect:
        # The client disconnected, so close the websocket
        await websocket.close()

async def get_chat_completion_stream(conversation, include_tools:bool):
    if include_tools:
        return await openai_client.chat.completions.create(
            model=default_ai().name,
            messages=conversation,
            stream=True,
            tools=nuclear_tools
        )
    else:
        return await openai_client.chat.completions.create(
            model=default_ai().name,
            messages=conversation,
            stream=True,
        )
