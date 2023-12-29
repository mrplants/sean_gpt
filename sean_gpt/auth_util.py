from datetime import datetime, timedelta
import uuid

from passlib.context import CryptContext
from jose import jwt

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Creates an OAuth2.0 access token.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (timedelta, optional): The amount of time until the token expires. Defaults to 15 minutes if None.
    
    Returns:
        str: The encoded token.
    """
    to_encode = data.copy()
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt