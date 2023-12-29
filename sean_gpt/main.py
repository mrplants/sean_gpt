import os

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

from .database import create_tables
from .routers import chat
from .routers import sms
from .routers import user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Configure the database on server start
    create_tables()
    yield
    # Shutdown logic

app = FastAPI(lifespan=lifespan)

app.include_router(user.router)

# Mount this last so that it doesn't override other routes
app.mount("/", StaticFiles(directory=os.path.dirname(__file__)+'/static/html', html=True), name="static")