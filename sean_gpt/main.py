import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import create_tables
from .routers import chats
from .routers import auth
from .routers import sms

app = FastAPI()

# configure the database on server start
@app.on_event("startup")
async def startup():
    create_tables()

app.include_router(chats.router)
app.include_router(auth.router)
app.include_router(sms.router)

# Mount this last so that it doesn't override other routes
app.mount("/", StaticFiles(directory=os.path.dirname(__file__)+'/static/html', html=True), name="static")