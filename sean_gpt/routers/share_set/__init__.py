""" Share_set Router
"""
from fastapi import APIRouter

from . import get, post, delete, modify

router = APIRouter(
    tags=["Share Sets"],
)

router.include_router(post.router)
router.include_router(get.router)
router.include_router(delete.router)
router.include_router(modify.router)
