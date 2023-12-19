import os

from fastapi import FastAPI

from .routers import chat_completions_openai
from .routers import authentication

app = FastAPI()
app.include_router(chat_completions_openai.router)
app.include_router(authentication.router)