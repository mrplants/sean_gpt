""" Share Set DELETE route. """
import uuid

from fastapi import APIRouter, status, HTTPException
from sqlmodel import select

from ...util.describe import describe
from ...util.user import AuthenticatedUserDep
from ...util.database import SessionDep
from ...model.file import ShareSet, File, FileShareSetLink

router = APIRouter(
    prefix="/share_set"
)

@describe(
""" Delete a Share Set.

Args:
    share_set_id (UUID): The id of the share set to delete.
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.
""")
@router.delete("/{share_set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share_set(# pylint: disable=missing-function-docstring
    share_set_id: uuid.UUID,
    session: SessionDep,
    current_user: AuthenticatedUserDep) -> None:
    # Cannot delete a share set if it is not owned by the current user
    share_set = session.exec(select(ShareSet).where(ShareSet.id == share_set_id)).first()
    if share_set.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share set not found.")
    # Cannot delete a default share set.  Search the files for this share set.
    if session.exec(select(File).where(File.default_share_set_id == share_set_id)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot delete default share set.")
    # Delete the associated file share set links
    file_share_set_links = session.exec(select(FileShareSetLink)
                                        .where(FileShareSetLink.share_set_id == share_set_id))
    for file_share_set_link in file_share_set_links:
        session.delete(file_share_set_link)
    session.commit()
    # Delete the share set
    session.delete(share_set)
    session.commit()
