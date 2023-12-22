from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select, Session

from ..model.authentication.user import User, UserData
from ..model.authentication.token import Token, TokenData
from ..config import settings
from ..database import db_engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="",
    tags=["Authentication"],
)

def verify_password(plain_password, hashed_password):
    """ Verifies a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """ Hashes a password.
    """
    return pwd_context.hash(password)

def get_user(email: str):
    """ Gets a user from the database.

    Args:
        email (str): The email of the user to get.  Emails cannot be shared between users.
    
    Returns:
        UserData: The user with the specified username or None.
    """
    with Session(db_engine) as session:
        return session.exec(select(UserData).where(UserData.email == email)).first()

def authenticate_user(email: str, password: str):
    """ Authenticates a user.
    
    Args:
        email (str): The email of the user to authenticate.
        password (str): The password of the user to authenticate.
        
    Returns:
        UserData: The user if the authentication is successful, otherwise None.
    """
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
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

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """ Gets the user from the database that is associated with this token.

    Args:
        token (str): The jwt encoded authentication token.
    
    Returns:
        UserData: The user associated with the token.
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

@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user