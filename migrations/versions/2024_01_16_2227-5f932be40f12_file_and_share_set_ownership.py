"""file and share set ownership

Revision ID: 5f932be40f12
Revises: 313d46ffeb68
Create Date: 2024-01-16 22:27:49.509134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '5f932be40f12'
down_revision: Union[str, None] = '313d46ffeb68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('file', sa.Column('owner_id', sqlmodel.sql.sqltypes.GUID(), nullable=False))
    op.create_index(op.f('ix_file_owner_id'), 'file', ['owner_id'], unique=False)
    op.create_foreign_key(None, 'file', 'authenticateduser', ['owner_id'], ['id'])
    op.add_column('shareset', sa.Column('owner_id', sqlmodel.sql.sqltypes.GUID(), nullable=False))
    op.create_index(op.f('ix_shareset_owner_id'), 'shareset', ['owner_id'], unique=False)
    op.create_foreign_key(None, 'shareset', 'authenticateduser', ['owner_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'shareset', type_='foreignkey')
    op.drop_index(op.f('ix_shareset_owner_id'), table_name='shareset')
    op.drop_column('shareset', 'owner_id')
    op.drop_constraint(None, 'file', type_='foreignkey')
    op.drop_index(op.f('ix_file_owner_id'), table_name='file')
    op.drop_column('file', 'owner_id')
    # ### end Alembic commands ###
