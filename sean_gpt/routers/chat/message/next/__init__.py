from fastapi import APIRouter

from . import post

router = APIRouter(
    tags=["Chat Completion"],
)

router.include_router(post.router)