from fastapi import APIRouter, status

from .util import AuthenticatedUserDep
from ...database import SessionDep
from ...util.describe import describe

router = APIRouter()

@describe(""" Delete the current user. """)
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def read_users_me(current_user: AuthenticatedUserDep, session: SessionDep):
    # Delete the user
    session.delete(current_user)
    session.commit()
    # Return nothing
    return None