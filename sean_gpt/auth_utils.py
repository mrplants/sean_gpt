from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select, Session

from .model.authentication.user import UserRead, AuthenticatedUser
from .model.authentication.token import Token, TokenData
from .config import settings
from .database import db_engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password:str, hashed_password:str) -> bool:
    """ Verifies a password against a hash.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password is correct, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password:str) -> str:
    """ Hashes a password.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)

def get_user(email: str) -> AuthenticatedUser | None:
    """ Gets a user from the database.

    Args:
        email (str): The email of the user to get.  Emails cannot be shared between users.
    
    Returns:
        AuthenticatedUser: The user with the specified username or None.
    """
    with Session(db_engine) as session:
        return session.exec(select(AuthenticatedUser).where(AuthenticatedUser.email == email)).first()

def authenticate_user(email: str, password: str) -> AuthenticatedUser | None:
    """ Authenticates a user.
    
    Args:
        email (str): The email of the user to authenticate.
        password (str): The password of the user to authenticate.
        
    Returns:
        AuthenticatedUser: The user if the authentication is successful, otherwise None.
    """
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Creates an OAuth2.0 access token.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (timedelta, optional): The amount of time until the token expires. Defaults to 15 minutes if None.
    
    Returns:
        str: The encoded token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

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
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.username)
    if user is None:
        raise credentials_exception
    return user

AuthenticatedUserDep = Annotated[UserRead, Security(get_current_user)]
