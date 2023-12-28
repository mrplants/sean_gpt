from datetime import timedelta
from typing import Annotated
import secrets

from fastapi import APIRouter, HTTPException, status, Security, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from ...config import constants, settings
from .util import authenticate_user, AuthenticatedUserDep
from ...auth_util import create_access_token, get_password_hash
from ...util.describe import describe
from ...model.authenticated_user import UserRead, AuthenticatedUser, UserCreate
from ...model.access_token import AccessToken
from ...model.verification_token import VerificationToken
from ...database import SessionDep
from ...sms import TwilioClientDep

router = APIRouter()

@describe(""" Creates a new user.

Args:
    phone (str): The user's phone number.
    password (str): The user's password.
    referral_code (str): The user's referral code.
          
Returns:
          UserRead: The user's information.
""")
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(*, user: UserCreate, referral_code: str = Body(), session: SessionDep) -> UserRead:
    # Check if the user exists
    select_user = select(AuthenticatedUser).where(AuthenticatedUser.phone == user.phone)
    existing_user = session.exec(select_user).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create user:  Phone already exists.",
        )
    # Check if the referral code exists
    select_referral = select(AuthenticatedUser).where(AuthenticatedUser.referral_code == referral_code)
    existing_referral = session.exec(select_referral).first()
    if not existing_referral:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create user:  Referral code does not exist.",
        )
    # Create the user
    user = AuthenticatedUser(phone=user.phone,
                             hashed_password=get_password_hash(user.password),
                             referrer_user_id=existing_referral.id)
    # Add the user to the database
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@describe(""" Authenticates a user and returns an OAuth2.0 access token.

Note the itentional swap of username and phone.  This is because the user's
phone is used as their username, but the OAuth2.0 spec uses the term
'username' instead of 'phone'.

Args:
    form_data (OAuth2PasswordRequestForm): The form data containing the username and password.

Returns:
    Token: The OAuth2.0 access token.
""")
@router.post("/token", response_model=AccessToken)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Security()]):
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

@describe(""" Requests a verification token be texted to the user's phone. """)
@router.post("/request_phone_verification")
def request_phone_verification(session: SessionDep, current_user: AuthenticatedUserDep, sms_client: TwilioClientDep):
    # Check if the user is already verified
    if current_user.is_phone_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already verified",
        )
    # Generate a verification token
    token_code = secrets.token_urlsafe(6)
    verification_token = VerificationToken(
        token_hash=get_password_hash(token_code),
        user_id=current_user.id)
    # Add the verification token to the database
    session.add(verification_token)
    session.commit()
    session.refresh(verification_token)
    # Send the verification token to the user
    sms_client.messages.create(
        body=constants.phone_verification_message.format(token_code),
        from_=settings.twilio_sid,
        to=current_user.phone,
    )
