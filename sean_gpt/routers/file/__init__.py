""" File Router
"""
from fastapi import APIRouter

from . import get, post, delete, processing_ws

router = APIRouter(
    tags=["Files"],
)

router.include_router(post.router)
router.include_router(get.router)
router.include_router(delete.router)
router.include_router(processing_ws.router)
