from fastapi import APIRouter

from ...model.authentication.user import UserRead
from .util import AuthenticatedUserDep

router = APIRouter()
@router.get("/users", response_model=UserRead)
async def read_users_me(current_user: AuthenticatedUserDep):
    """ Gets the current user.

    Args:
        current_user (UserRead): The current user.
    """
    return current_user