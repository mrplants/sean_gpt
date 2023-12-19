import requests
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends

from ..model.chat_completion.chat_request import ChatRequest
from ..model.authentication.user import User
from .authentication import get_current_user
from ..config import settings

router = APIRouter(
    prefix="/chat/completions/openai",
    tags=["Chat Completion"],
)

@router.post("/", dependencies=[Depends(get_current_user)])
def openai_chat_completions(request: ChatRequest):
    """ Passes the request verbatim to the OpenAI API.

    Args:
        request (ChatRequest): The request to pass to the OpenAI API.

    Returns:
        Response from OpenAI API.
    """
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(settings.openai_api_url, json=request.dict(), headers=headers)
        response.raise_for_status()  # Will raise HTTPError for 4xx/5xx responses
        return response.json()
    except requests.exceptions.HTTPError as err:
        raise HTTPException(status_code=response.status_code, detail=str(err))
