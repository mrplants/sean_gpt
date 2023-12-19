import os

from fastapi import FastAPI

from .settings import Settings
from .routers import chat_completions_openai

app = FastAPI()
app.include_router(chat_completions_openai.router)


@app.on_event("startup")
def startup_event():
    # Load environment variables from a .env file
    app.state.settings = Settings()