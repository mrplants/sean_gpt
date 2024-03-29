""" Delete the current user. """
from fastapi import APIRouter, status

from ...util.user import AuthenticatedUserDep
from ...util.database import SessionDep
from ...util.describe import describe

router = APIRouter(prefix="/user")

@describe(""" Delete the current user. """)
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def read_users_me(current_user: AuthenticatedUserDep, session: SessionDep): # pylint: disable=missing-function-docstring
    # Delete the user
    session.delete(current_user)
    session.commit()
    # Return nothing
    return None
