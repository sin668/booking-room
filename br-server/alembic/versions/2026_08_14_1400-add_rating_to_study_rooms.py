"""add_rating_to_study_rooms

Revision ID: e3f4a5b6c7d8
Revises: f61f3ab400f5
Create Date: 2026-08-14 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "f61f3ab400f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("study_rooms",
        sa.Column("rating", sa.Numeric(3, 1), server_default="0.0", nullable=False))


def downgrade() -> None:
    op.drop_column("study_rooms", "rating")
