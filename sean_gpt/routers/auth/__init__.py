from fastapi import APIRouter

from . import auth

router = APIRouter(
    prefix="",
    tags=["Authentication"],
)

router.include_router(auth.router)