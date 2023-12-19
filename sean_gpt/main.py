import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import chat_completions_openai
from .routers import authentication

app = FastAPI()
app.include_router(chat_completions_openai.router)
app.include_router(authentication.router)
app.mount("/", StaticFiles(directory=os.path.dirname(__file__)+'/static/html', html=True), name="static")