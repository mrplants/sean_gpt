from fastapi import APIRouter

from . import post, delete

router = APIRouter(
    prefix="/users",
    tags=["Authentication"],
)

router.include_router(post.router)
router.include_router(delete.router)