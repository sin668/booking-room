"""add teacher bio and student_count

Revision ID: a1b2c3d4e5f6
Revises: c84abd1322d4
Create Date: 2026-08-17 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c84abd1322d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teachers', sa.Column('bio', sa.String(1000), nullable=True))
    op.add_column('teachers', sa.Column('student_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('teachers', 'student_count')
    op.drop_column('teachers', 'bio')
