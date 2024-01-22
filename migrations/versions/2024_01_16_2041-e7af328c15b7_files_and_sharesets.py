"""files_and_sharesets

Revision ID: e7af328c15b7
Revises: 1a8c09642471
Create Date: 2024-01-16 20:41:47.830925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e7af328c15b7'
down_revision: Union[str, None] = '1a8c09642471'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('shareset',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('file',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('default_share_set_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('uploaded_at', sa.Integer(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['default_share_set_id'], ['shareset.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_default_share_set_id'), 'file', ['default_share_set_id'], unique=False)
    op.create_index(op.f('ix_file_uploaded_at'), 'file', ['uploaded_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_file_uploaded_at'), table_name='file')
    op.drop_index(op.f('ix_file_default_share_set_id'), table_name='file')
    op.drop_table('file')
    op.drop_table('shareset')
    # ### end Alembic commands ###
