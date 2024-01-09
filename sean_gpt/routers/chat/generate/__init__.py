from fastapi import APIRouter

from . import post, get

router = APIRouter(
    tags=["Chat Completion"],
)

router.include_router(post.router)
router.include_router(get.router)