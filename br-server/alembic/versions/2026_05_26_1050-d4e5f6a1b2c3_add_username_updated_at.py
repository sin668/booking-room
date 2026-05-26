"""add_username_updated_at

Adds users.username_updated_at and backfills existing users that still have
NULL username values before enforcing users.username as NOT NULL. The existing
ix_users_username index is already a global unique index for non-null usernames,
so this migration does not create or replace username indexes.

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-05-26 10:50:00.000000

"""
from typing import Sequence, Union

import random

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a1b2c3"
down_revision: Union[str, None] = "c3d4e5f6a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENGLISH_NAMES = (
    "Luna",
    "Mia",
    "Noah",
    "Ava",
    "Leo",
    "Ivy",
    "Eli",
    "Zoe",
    "Nina",
    "Owen",
    "Ruby",
    "Milo",
    "Emma",
    "Liam",
    "Aria",
    "Jack",
)


def _generate_username(used: set[str]) -> str:
    for _ in range(1000):
        candidate = f"{random.choice(ENGLISH_NAMES)}{random.randint(10000, 99999)}"
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise RuntimeError("Unable to generate a unique username during migration")


def upgrade() -> None:
    op.add_column("users", sa.Column("username_updated_at", sa.DateTime(), nullable=True))

    connection = op.get_bind()
    used = {
        row[0]
        for row in connection.execute(sa.text("SELECT username FROM users WHERE username IS NOT NULL"))
    }
    rows = connection.execute(
        sa.text("SELECT id FROM users WHERE username IS NULL")
    ).fetchall()

    for row in rows:
        username = _generate_username(used)
        connection.execute(
            sa.text("UPDATE users SET username = :username WHERE id = :id"),
            {"username": username, "id": row[0]},
        )

    op.alter_column("users", "username", existing_type=sa.String(length=50), nullable=False)


def downgrade() -> None:
    op.alter_column("users", "username", existing_type=sa.String(length=50), nullable=True)
    op.drop_column("users", "username_updated_at")
