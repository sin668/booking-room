"""add_teacher_available_time_slots

Revision ID: 97bc597327c1
Revises: 7a8b9c0d1e2f
Create Date: 2026-08-31 09:28:28.017588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97bc597327c1'
down_revision: Union[str, None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teachers', sa.Column('available_time_slots', sa.Text(), nullable=True, comment='可排课时间段，JSON 数组格式'))


def downgrade() -> None:
    op.drop_column('teachers', 'available_time_slots')
