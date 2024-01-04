from typing import Annotated

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import select, Session

from ...model.authenticated_user import UserRead, AuthenticatedUser
from ...model.access_token import AccessTokenData
from ...config import settings
from ...database import get_db_engine
from ...util.auth import verify_password
from ...util.describe import describe
from ...database import SessionDep

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")

def get_user(phone: str) -> AuthenticatedUser | None:
    """ Gets a user from the database.

    Args:
        phone (str): The phone of the user to get.  phones cannot be shared between users.
    
    Returns:
        AuthenticatedUser: The user with the specified username or None.
    """
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        return session.exec(select(AuthenticatedUser).where(AuthenticatedUser.phone == phone)).first()

def authenticate_user(phone: str, password: str) -> AuthenticatedUser | None:
    """ Authenticates a user.
    
    Args:
        phone (str): The phone of the user to authenticate.
        password (str): The password of the user to authenticate.
        
    Returns:
        AuthenticatedUser: The user if the authentication is successful, otherwise None.
    """
    user = get_user(phone)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> AuthenticatedUser:
    """ Gets the user from the database that is associated with this token.

    Args:
        token (str): The jwt encoded authentication token.
    
    Returns:
        AuthenticatedUser: The user associated with the token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # The jwt.decode method automatically checks the expiration of the JWT.
        # The 'exp' claim in the JWT is a Unix timestamp of when the token expires.
        # If the current time is past this expiration time, jwt.decode raises a JWTError.
        # This is a built-in feature of the python-jose library, ensuring expired tokens are rejected.
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = AccessTokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(phone=token_data.username)
    if user is None:
        raise credentials_exception
    return user

AuthenticatedUserDep = Annotated[UserRead, Security(get_current_user)]

def current_user_verified(user: AuthenticatedUserDep):
    """ Checks if the user is verified.

    Raises:
        HTTPException: If the user is not verified.

    Args:
        user (AuthenticatedUserDep): The user to check.
    """
    if not user.is_phone_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phone is not verified.")

IsVerifiedUserDep = Depends(current_user_verified)