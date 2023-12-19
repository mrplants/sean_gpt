import requests

from fastapi import APIRouter, HTTPException, Request, Depends

from ..model.chat_request import ChatRequest
from ..settings import Settings

router = APIRouter(
    prefix="/chat/completions/openai",
    tags=["Chat Completion"],
)

def get_settings(request: Request):
    return request.app.state.settings

@router.post("/")
def openai_chat_completions(request: ChatRequest, settings: Settings = Depends(get_settings)):
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
