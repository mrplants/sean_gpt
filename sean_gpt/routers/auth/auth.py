from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm

from ...model.authentication.user import UserRead
from ...model.authentication.token import Token
from ...config import settings
from .utils import authenticate_user, create_access_token, AuthenticatedUserDep

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """ Authenticates a user and returns an OAuth2.0 access token.

    Note the itentional swap of username and email.  This is because the user's
    email is used as their username, but the OAuth2.0 spec uses the term
    'username' instead of 'email'.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the username and password.
    
    Returns:
        Token: The OAuth2.0 access token.
    """
    user = authenticate_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=float(settings.access_token_expire_minutes))
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", response_model=UserRead)
async def read_users_me(current_user: AuthenticatedUserDep):
    """ Gets the current user.

    Args:
        current_user (UserRead): The current user.
    """
    return current_user