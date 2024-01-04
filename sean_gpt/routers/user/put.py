from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, status, HTTPException, Body
from pydantic import BaseModel
from sqlmodel import select

from ...util.describe import describe
from .util import AuthenticatedUserDep
from ...util.auth import verify_password, get_password_hash
from ...database import SessionDep
from ...model.authenticated_user import AuthenticatedUser

router = APIRouter(prefix="/user")

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
            detail="Unable to change password:  Incorrect password."
        )
    # Retrieve the previous hashed password
    old_password_hash = current_user.hashed_password
    new_password_hash = get_password_hash(change_request.new_password)
    # Change the password
    current_user.hashed_password = new_password_hash
    session.add(current_user)
    session.commit()
    check_current_user = session.exec(select(AuthenticatedUser).where(AuthenticatedUser.id == current_user.id)).first()
    # Check that the password has been changed
    if check_current_user.hashed_password != new_password_hash:
        check_current_user.hashed_password = old_password_hash
        session.add(check_current_user)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password has not been changed."
        )

@describe(
""" Set the is_phone_verified status of the current user to True.

This endpoint requires the user to be authenticated. It also requires the user
to provide their unexpired verification code.

Args:
    phone_verification_code (str): The verification code.
""")
@router.put("/is_phone_verified", status_code=status.HTTP_204_NO_CONTENT)
def verify_phone(*,
    phone_verification_code: str = Body(embed=True),
    current_user: AuthenticatedUserDep,
    session: SessionDep
    ):
    session.add(current_user)
    # We know that the authentication token is valid because the user is authenticated.
    # Check that the user has a verification token
    if not current_user.verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to verify phone:  Invalid verification code."
        )
    # Check the verification code using the cryptographic hash comparison function
    print(f'current_user.verification_token: {current_user.verification_token}')
    if not verify_password(phone_verification_code, current_user.verification_token.code_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to verify phone:  Invalid verification code."
        )
    # Check that the verification code is not expired
    if current_user.verification_token.expiration < datetime.now().timestamp():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to verify phone:  Invalid verification code."
        )
    # Set the phone verification status to True
    current_user.is_phone_verified = True
    session.commit()
    # Check that the phone verification status has been changed
    check_current_user = session.exec(select(AuthenticatedUser).where(AuthenticatedUser.id == current_user.id)).first()
    if check_current_user.is_phone_verified != True:
        check_current_user.is_phone_verified = False
        session.add(check_current_user)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Phone verification status has not been changed."
        )
    # Delete the verification token now that it has been used
    session.delete(current_user.verification_token)
    session.commit()