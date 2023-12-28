from fastapi import APIRouter

from ...model.authenticated_user import UserRead
from .util import AuthenticatedUserDep

router = APIRouter()
@router.delete("/")
async def read_users_me(current_user: AuthenticatedUserDep):
    """ Delete the current user. """
    pass