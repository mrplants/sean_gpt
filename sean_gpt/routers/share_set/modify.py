""" ShareSet PATCH routes. """
from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Body
from sqlmodel import select

from ...util.describe import describe
from ...util.user import AuthenticatedUserDep
from ...util.database import SessionDep
from ...model.file import ShareSet, FileShareSetLink, File

router = APIRouter(
    prefix="/share_set"
)

@describe(
""" Update a share set name.

Args:
    share_set_id (UUID): The id of the share set to update.
    name (str): The new name of the share set.
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.

Returns:
    The updated share set.
""")
@router.patch("/{share_set_id}")
async def patch_share_set(# pylint: disable=missing-function-docstring
    *,
    share_set_id: str,
    name: Annotated[str | None, Body(embed=True)] = None,
    is_public: Annotated[bool | None, Body(embed=True)] = None,
    session: SessionDep,
    current_user: AuthenticatedUserDep) -> ShareSet:
    share_set = session.exec(select(ShareSet).where(ShareSet.id == share_set_id)).first()
    # Cannot update a share set if it is not owned by the current user
    if share_set is None or share_set.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share set not found.")
    if name is not None:
        share_set.name = name
    if is_public is not None:
        share_set.is_public = is_public
    if name is None and is_public is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update.")
    session.add(share_set)
    session.commit()
    session.refresh(share_set)
    return share_set

@describe(
""" Add a file to a share set.

Args:
    share_set_id (UUID): The id of the share set to update.
    file_id (UUID): The id of the file to add to the share set.
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.
""")
@router.post("/{share_set_id}/file/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def post_share_set_file(# pylint: disable=missing-function-docstring
    *,
    share_set_id: str,
    file_id: str,
    session: SessionDep,
    current_user: AuthenticatedUserDep) -> None:
    share_set = session.exec(select(ShareSet).where(ShareSet.id == share_set_id)).first()
    # Cannot update a share set if it is not owned by the current user
    if share_set is None or share_set.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share set not found.")
    # Cannot associate a file unless:
    #   1. The file is owned by the current user OR
    #   2. The file is public
    # A public file has a default share set that is public.
    file = session.exec(select(File).where(File.id == file_id)).first()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    if file.owner_id != current_user.id:
        default_share_set = session.exec(select(ShareSet).where(ShareSet.id ==
                                                                file.default_share_set_id)).first()
        if not default_share_set.is_public:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    # Create a link between the file and the share set
    link = FileShareSetLink(file_id=file_id, share_set_id=share_set_id)
    session.add(link)
    session.commit()

@describe(
""" Remove a file from a share set.

Args:
    share_set_id (UUID): The id of the share set to update.
    file_id (UUID): The id of the file to remove from the share set.
    session (SessionDep): The database session.
    current_user (AuthenticatedUserDep): The current user.
""")
@router.delete("/{share_set_id}/file/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share_set_file(# pylint: disable=missing-function-docstring
    *,
    share_set_id: str,
    file_id: str,
    session: SessionDep,
    current_user: AuthenticatedUserDep) -> None:
    share_set = session.exec(select(ShareSet).where(ShareSet.id == share_set_id)).first()
    # Cannot update a share set if it is not owned by the current user
    if share_set is None or share_set.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share set not found.")
    # Cannot remove a file unless:
    #   1. The file is owned by the current user OR
    #   2. The file is public
    # A public file has a default share set that is public.
    file = session.exec(select(File).where(File.id == file_id)).first()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    if file.owner_id != current_user.id:
        default_share_set = session.exec(select(ShareSet).where(ShareSet.id ==
                                                                file.default_share_set_id)).first()
        if not default_share_set.is_public:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    # Delete the link between the file and the share set
    link = session.exec(select(FileShareSetLink)
                        .where(FileShareSetLink.file_id == file_id,
                               FileShareSetLink.share_set_id == share_set_id)).first()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="File not found in share set.")
    session.delete(link)
    session.commit()
