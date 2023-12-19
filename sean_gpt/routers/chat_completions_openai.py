import requests

from fastapi import APIRouter, HTTPException

from ..model.chat_request import ChatRequest

router = APIRouter(
    prefix="/chat/completions/openai",
    tags=["Chat Completion"],
)

@router.post("/")
def openai_chat_completions(request: ChatRequest):
    """ Passes the request verbatim to the OpenAI API.

    Args:
        request (ChatRequest): The request to pass to the OpenAI API.

    Returns:
        Response from OpenAI API.
    """
    headers = {
        "Authorization": f"Bearer {request.app.state.settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(request.app.state.settings.OPENAI_API_URL, json=request.dict(), headers=headers)
        response.raise_for_status()  # Will raise HTTPError for 4xx/5xx responses
        return response.json()
    except requests.exceptions.HTTPError as err:
        raise HTTPException(status_code=response.status_code, detail=str(err))
