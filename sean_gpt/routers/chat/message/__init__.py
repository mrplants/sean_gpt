from fastapi import APIRouter

from . import get, post, next

router = APIRouter(
    tags=["Chat Completion"],
)

router.include_router(get.router)
router.include_router(post.router)

router.include_router(next.router, prefix="/message")