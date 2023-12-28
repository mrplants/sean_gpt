from fastapi import APIRouter

from ...model.authentication.user import UserRead
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
    return {"referral_code": current_user.referral_code}