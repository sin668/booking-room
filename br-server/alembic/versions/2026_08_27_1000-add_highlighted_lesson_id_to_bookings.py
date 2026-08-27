"""add highlighted_lesson_id to bookings

Revision ID: 7a8b9c0d1e2f
Revises: f5a6b7c8d9e0
Create Date: 2026-08-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: str = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bookings',
        sa.Column(
            'highlighted_lesson_id',
            sa.Integer(),
            nullable=True,
            comment='当前高亮的课时ID（课程预约）',
        ),
    )


def downgrade() -> None:
    op.drop_column('bookings', 'highlighted_lesson_id')
