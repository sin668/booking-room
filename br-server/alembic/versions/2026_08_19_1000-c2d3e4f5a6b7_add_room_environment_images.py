"""add environment_images to study_rooms

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-08-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "study_rooms",
        sa.Column(
            "environment_images",
            sa.JSON,
            nullable=True,
            comment="环境图片 URL 列表，最多 5 张",
        ),
    )


def downgrade() -> None:
    op.drop_column("study_rooms", "environment_images")
