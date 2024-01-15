"""Initial Migration

Revision ID: b552fc6476cd
Revises: 
Create Date: 2024-01-14 21:46:09.866864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b552fc6476cd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ai',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_name'), 'ai', ['name'], unique=True)
    op.create_table('authenticateduser',
    sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('referral_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_phone_verified', sa.Boolean(), nullable=False),
    sa.Column('referrer_user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('twilio_chat_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_authenticateduser_phone'), 'authenticateduser', ['phone'], unique=True)
    op.create_index(op.f('ix_authenticateduser_referral_code'), 'authenticateduser', ['referral_code'], unique=True)
    op.create_index(op.f('ix_authenticateduser_referrer_user_id'), 'authenticateduser', ['referrer_user_id'], unique=False)
    op.create_table('chat',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('assistant_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('is_assistant_responding', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['assistant_id'], ['ai.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['authenticateduser.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_assistant_id'), 'chat', ['assistant_id'], unique=False)
    op.create_index(op.f('ix_chat_user_id'), 'chat', ['user_id'], unique=False)
    op.create_table('verificationtoken',
    sa.Column('code_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('expiration', sa.Integer(), nullable=False),
    sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['authenticateduser.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verificationtoken_code_hash'), 'verificationtoken', ['code_hash'], unique=True)
    op.create_table('message',
    sa.Column('role', sa.Enum('user', 'assistant', name='roletype'), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('chat_index', sa.Integer(), nullable=False),
    sa.Column('chat_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_chat_id'), 'message', ['chat_id'], unique=False)
    op.create_index(op.f('ix_message_created_at'), 'message', ['created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_message_created_at'), table_name='message')
    op.drop_index(op.f('ix_message_chat_id'), table_name='message')
    op.drop_table('message')
    op.drop_index(op.f('ix_verificationtoken_code_hash'), table_name='verificationtoken')
    op.drop_table('verificationtoken')
    op.drop_index(op.f('ix_chat_user_id'), table_name='chat')
    op.drop_index(op.f('ix_chat_assistant_id'), table_name='chat')
    op.drop_table('chat')
    op.drop_index(op.f('ix_authenticateduser_referrer_user_id'), table_name='authenticateduser')
    op.drop_index(op.f('ix_authenticateduser_referral_code'), table_name='authenticateduser')
    op.drop_index(op.f('ix_authenticateduser_phone'), table_name='authenticateduser')
    op.drop_table('authenticateduser')
    op.drop_index(op.f('ix_ai_name'), table_name='ai')
    op.drop_table('ai')
    # ### end Alembic commands ###
