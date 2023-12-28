from datetime import timedelta
from typing import Annotated
import logging

from fastapi import APIRouter, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from ...model.authentication.token import Token
from ...config import settings
from .util import authenticate_user
from ...auth_util import create_access_token
from ...util.describe import describe
from ...model.authentication.user import UserRead, AuthenticatedUser
from ...database import SessionDep
from ...auth_util import get_password_hash

router = APIRouter()

@describe(""" Creates a new user.

Args:
    phone (str): The user's phone number.
    password (str): The user's password.
    referral_code (str): The user's referral code.
          
Returns:
          UserRead: The user's information.
""")
@router.post("/")
def create_user(phone: str, password: str, referral_code: str, session: SessionDep) -> UserRead:
    # Check if the user exists
    select_user = select(AuthenticatedUser).where(AuthenticatedUser.phone == phone)
    existing_user = session.exec(select_user).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )
    # Check if the referral code exists
    select_referral = select(AuthenticatedUser).where(AuthenticatedUser.referral_code == referral_code)
    existing_referral = session.exec(select_referral).first()
    if not existing_referral:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Referral code does not exist",
        )
    # Create the user
    user = AuthenticatedUser(phone=phone, hashed_password=get_password_hash(password))
    # Add the user to the database
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Security()]):
    """ Authenticates a user and returns an OAuth2.0 access token.

    Note the itentional swap of username and phone.  This is because the user's
    phone is used as their username, but the OAuth2.0 spec uses the term
    'username' instead of 'phone'.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the username and password.
    
    Returns:
        Token: The OAuth2.0 access token.
    """
    user = authenticate_user(phone=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=float(settings.access_token_expire_minutes))
    access_token = create_access_token(
        data={"sub": user.phone}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
