""" Main entrypoint for the Sean GPT API. 
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .util.database import (
    reset_db_connection, create_admin_if_necessary, create_milvus_collection_if_necessary)
from .routers import chat
from .routers import user
from .routers import twilio
from .routers import generate
from .routers import file
from .routers import share_set
from .util.user import IsVerifiedUserDep

if os.environ.get('SEAN_GPT_DEBUG', '0') == '1':
    from .routers import mock

@asynccontextmanager
async def lifespan(_): # pylint: disable=missing-function-docstring
    # Startup logic
    reset_db_connection()
    create_milvus_collection_if_necessary()
    create_admin_if_necessary()
    if os.environ.get('SEAN_GPT_DEBUG', '0') == '1':
        mock.startup()
    yield
    if os.environ.get('SEAN_GPT_DEBUG', '0') == '1':
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
app.include_router(file.router)
app.include_router(share_set.router)

@app.get("/health")
async def health_check():
    """ Health check endpoint.
    """
    return {"status": "ok"}

if os.environ.get('SEAN_GPT_DEBUG', '0') == '1':
    app.include_router(mock.router)
