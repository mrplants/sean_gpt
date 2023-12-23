from fastapi import APIRouter

from . import get, post

router = APIRouter(
    prefix="/chats",
    tags=["Chat Completion"],
)

router.include_router(get.router)
router.include_router(post.router)