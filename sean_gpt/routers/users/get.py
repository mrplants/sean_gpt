from fastapi import APIRouter, HTTPException

from ...model.authenticated_user import UserRead
from .util import AuthenticatedUserDep
from ...util.describe import describe

router = APIRouter()

@describe(""" Gets the current user.

Args:
    current_user (UserRead): The current user.

Returns:
    UserRead: The current user.
""")
@router.get("/")
def read_users_me(current_user: AuthenticatedUserDep) -> UserRead:
    return current_user

@describe(""" Retrieve the user's referral code.

Args:
    current_user (UserRead): The current user.
          
Returns:
    dict: The user's referral code.
""")
@router.get("/referral_code")
def get_referral_code(current_user: AuthenticatedUserDep) -> dict:
    # Referral codes can only be retrieved if the user is_phone_verified
    if not current_user.is_phone_verified:
        raise HTTPException(status_code=400, detail="Unable to retrieve referral code:  Phone is not verified.")
    return {"referral_code": current_user.referral_code}