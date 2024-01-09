""" Chat Completion Router
"""
from fastapi import APIRouter

from . import get, post, put, delete
from . import message, generate

router = APIRouter(
    tags=["Chat Completion"],
)

router.include_router(get.router)
router.include_router(post.router)
router.include_router(put.router)
router.include_router(delete.router)

router.include_router(message.router, prefix="/chat")
router.include_router(generate.router, prefix="/chat")
