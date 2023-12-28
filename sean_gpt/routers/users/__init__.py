from fastapi import APIRouter

from . import post, delete, get

router = APIRouter(
    prefix="/users",
    tags=["Authentication"],
)

router.include_router(post.router)
router.include_router(delete.router)
router.include_router(get.router)