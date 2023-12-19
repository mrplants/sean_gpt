from typing import List
from pydantic import BaseModel
from .message import Message

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
