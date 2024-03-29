""" User router. """
from fastapi import APIRouter

from . import post, delete, get, put

router = APIRouter(
    tags=["Authentication"],
)

router.include_router(post.router)
router.include_router(delete.router)
router.include_router(get.router)
router.include_router(put.router)
