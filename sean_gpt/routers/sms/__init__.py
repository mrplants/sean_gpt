from fastapi import APIRouter

from . import post

router = APIRouter(
    prefix="/sms",
    tags=["SMS"],
)

router.include_router(post.router)