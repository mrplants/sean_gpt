""" Chat Completion Router """
from fastapi import APIRouter

from . import chat_ws, get

router = APIRouter(
    tags=["Chat Completion"],
)

router.include_router(chat_ws.router)
router.include_router(get.router)
