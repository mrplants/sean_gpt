from fastapi import APIRouter

from ...model.authentication.user import UserRead
from .util import AuthenticatedUserDep

router = APIRouter()
@router.delete("/users")
async def read_users_me(current_user: AuthenticatedUserDep):
    """ Delete the current user. """
    pass