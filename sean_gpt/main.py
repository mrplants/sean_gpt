""" Main entrypoint for the Sean GPT API. 
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .util.database import reset_db_connection
from .routers import chat
from .routers import user
from .routers import twilio
from .routers import generate
from .util.user import IsVerifiedUserDep

if 'DEBUG_MOCK' in os.environ and os.environ['DEBUG_MOCK']:
    from .routers import mock

@asynccontextmanager
async def lifespan(_): # pylint: disable=missing-function-docstring
    # Startup logic
    reset_db_connection()
    if 'DEBUG_MOCK' in os.environ and os.environ['DEBUG_MOCK']:
        mock.startup()
    yield
    if 'DEBUG_MOCK' in os.environ and os.environ['DEBUG_MOCK']:
        mock.shutdown()
    # Shutdown logic

app = FastAPI(lifespan=lifespan)

origins = [
    "https://sean-gpt.com",
    "https://dev.sean-gpt.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(chat.router, dependencies=[IsVerifiedUserDep])
app.include_router(twilio.router)
app.include_router(generate.router)

@app.get("/health")
async def health_check():
    """ Health check endpoint.
    """
    return {"status": "ok"}

if 'DEBUG_MOCK' in os.environ and os.environ['DEBUG_MOCK']:
    app.include_router(mock.router)
