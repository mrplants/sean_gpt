from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel

from ...util.describe import describe
from .util import AuthenticatedUserDep
from ...auth_util import verify_password, get_password_hash
from ...database import SessionDep

router = APIRouter()

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

@describe(
""" Changes a user's password.

Changing a user's password requires the user to be authenticated. It also
requires the user to provide their old password.

Args:
    new_password (str): The new password.
    old_password (str): The old password.
""")
@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    change_request: PasswordChangeRequest,
    current_user: AuthenticatedUserDep,
    session: SessionDep
    ):
    # We know that the authentication token is valid because the user is authenticated.
    # Check the old password
    if not verify_password(change_request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password."
        )
    # Change the password
    current_user.hashed_password = get_password_hash(change_request.new_password)
    session.commit()