""" Share Set GET Routes.
"""
import uuid
from typing import List, Union, Annotated

from fastapi import APIRouter, Query
from sqlmodel import select

from ...util.user import AuthenticatedUserDep
from ...util.database import SessionDep
from ...util.describe import describe
from ...model.file import ShareSet, FileShareSetLink

router = APIRouter(
    prefix="/share_set"
)

@describe(
""" Get a list of share sets.

Args:
    file_id (UUID): The id of the file to retrieve.
    share_set_id (UUID): The id of the share set to retrieve.
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.
""")
@router.get("")
async def get_share_sets(# pylint: disable=missing-function-docstring
    *,
    file_id: Annotated[Union[uuid.UUID, None], Query()] = None,
    share_set_id: Annotated[uuid.UUID | None, Query()] = None,
    session: SessionDep,
    current_user: AuthenticatedUserDep) -> List[ShareSet]:
    # Important:  A share set can only be retrieved if the user is the owner or the share set is
    #             public.
    # Start a cascading filter query
    query = select(ShareSet)
    # First, filter by file id if provided.
    # This requires a join on the file share set link table.
    if file_id is not None:
        query = select(ShareSet).join(FileShareSetLink).where(FileShareSetLink.file_id == file_id)
    # Next, filter by share set id if provided
    if share_set_id is not None:
        query = query.where(ShareSet.id == share_set_id)

    # Finally, continue to filter share sets by current owner or public
    query = query.where((ShareSet.owner_id == current_user.id) | (ShareSet.is_public))

    return session.exec(query).all()
