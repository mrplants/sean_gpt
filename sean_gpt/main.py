""" Main entrypoint for the Sean GPT API. 
"""

import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .util.database import create_tables_if_necessary, reset_db_connection
from .routers import chat
from .routers import user
from .routers import twilio
from .routers import generate
from .routers.user.util import IsVerifiedUserDep

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    reset_db_connection()
    create_tables_if_necessary()
    yield
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