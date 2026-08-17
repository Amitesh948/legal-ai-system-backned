"""add client rating to case

Revision ID: ddb1b28f4441
Revises: 326e11b48d5e
Create Date: 2026-08-17 05:07:30.494429+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddb1b28f4441'
down_revision: Union[str, None] = '326e11b48d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cases', sa.Column('client_rating', sa.Integer(), nullable=True))
    op.add_column('cases', sa.Column('client_review', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('cases', 'client_review')
    op.drop_column('cases', 'client_rating')
