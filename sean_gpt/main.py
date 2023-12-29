import os

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

from .database import create_tables_if_necessary, reset_db_connection
from .routers import chat
from .routers import user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    reset_db_connection()
    create_tables_if_necessary()
    yield
    # Shutdown logic

app = FastAPI(lifespan=lifespan)

app.include_router(user.router)
app.include_router(chat.router)

# Mount this last so that it doesn't override other routes
app.mount("/", StaticFiles(directory=os.path.dirname(__file__)+'/static/html', html=True), name="static")