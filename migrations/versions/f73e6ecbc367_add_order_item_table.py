"""Add Order Item Table

Revision ID: f73e6ecbc367
Revises: 5c1bf390fc38
Create Date: 2025-02-06 17:11:34.233952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'f73e6ecbc367'
down_revision: Union[str, None] = '5c1bf390fc38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('orderItems',
    sa.Column('uid', sa.UUID(), nullable=False),
    sa.Column('order_id', sa.UUID(), nullable=False),
    sa.Column('item_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.INTEGER(), nullable=False),
    sa.Column('price_at_order_time', sa.NUMERIC(precision=10, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['items.uid'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.uid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('uid')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('orderItems')
    # ### end Alembic commands ###
