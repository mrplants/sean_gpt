""" Share Set POST Routes.
"""
from typing import Annotated

from fastapi import APIRouter, Body

from ...model.file import ShareSet
from ...util.describe import describe
from ...util.user import AuthenticatedUserDep
from ...util.database import SessionDep

router = APIRouter(
    prefix="/share_set"
)

@describe(
""" Create a new share set.

Args:
    name (str): The name of the share set, optional
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.

Returns:
    ShareSet: The created share set.
""")
@router.post("")
async def create_share_set(# pylint: disable=missing-function-docstring
    *,
    name: Annotated[str | None, Body(embed=True)] = None,
    session: SessionDep,
    current_user: AuthenticatedUserDep) -> ShareSet:
    # Create the share set
    share_set = ShareSet(name=name if name else "", owner_id=current_user.id)
    session.add(share_set)
    session.commit()
    session.refresh(share_set)
    return share_set