"""Init migration

Revision ID: ae99fd974d69
Revises: 
Create Date: 2025-06-06 14:09:36.685284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae99fd974d69'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cultures',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('adress', sa.String(), nullable=False),
    sa.Column('date_time', sa.String(), nullable=False),
    sa.Column('desc', sa.String(), nullable=False),
    sa.Column('ya_card', sa.String(), nullable=False),
    sa.Column('site', sa.String(), nullable=False),
    sa.Column('up_five', sa.Boolean(), nullable=False),
    sa.Column('up_hundred', sa.Boolean(), nullable=False),
    sa.Column('is_museum', sa.Boolean(), nullable=False),
    sa.Column('is_park', sa.Boolean(), nullable=False),
    sa.Column('is_delicious', sa.Boolean(), nullable=False),
    sa.Column('is_all_day', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('messages_for_users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('who', sa.String(), nullable=False),
    sa.Column('tg_username', sa.String(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('text_for_message', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=False),
    sa.Column('tg_username', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tg_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('messages_for_users')
    op.drop_table('cultures')
    # ### end Alembic commands ###
