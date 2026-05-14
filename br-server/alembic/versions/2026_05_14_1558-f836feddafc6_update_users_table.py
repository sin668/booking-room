"""update_users_table

Revision ID: f836feddafc6
Revises: 28a1f4af90df
Create Date: 2026-05-14 15:58:15.530495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f836feddafc6'
down_revision: Union[str, None] = '28a1f4af90df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('UPDATE users SET balance = 0 WHERE balance IS NULL')

    if op.get_bind().dialect.name == 'sqlite':
        with op.batch_alter_table('users') as batch_op:
            batch_op.alter_column(
                'balance',
                existing_type=sa.NUMERIC(precision=10, scale=2),
                existing_server_default='0',
                nullable=False,
            )
    else:
        op.alter_column(
            'users',
            'balance',
            existing_type=sa.NUMERIC(precision=10, scale=2),
            existing_server_default='0',
            nullable=False,
        )


def downgrade() -> None:
    # The previous revision already defines users.balance as NOT NULL with a
    # default. Downgrading this safety backfill revision should leave that
    # schema intact.
    pass
