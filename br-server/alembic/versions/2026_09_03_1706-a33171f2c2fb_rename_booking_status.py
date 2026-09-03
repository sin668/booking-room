"""rename booking status

Revision ID: a33171f2c2fb
Revises: f6a7b8c9d0e1
Create Date: 2026-09-03 17:06:37.140535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a33171f2c2fb'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 显式限定 status 列，绝不触碰 payment_status（其 pending 语义为「待支付」，跨域同名值）。
    # 幂等：WHERE 只命中旧值，重跑无副作用，可在新旧值混存后重跑收敛。
    # 方言中立：纯 SQL UPDATE 在 PostgreSQL（生产）与 SQLite（测试）均可执行；零 DDL（status 为裸 String(20)，无 enum/CHECK）。
    op.execute("UPDATE bookings SET status='pending_start' WHERE status='pending'")
    op.execute("UPDATE bookings SET status='in_progress' WHERE status='confirmed'")


def downgrade() -> None:
    # 反向 UPDATE，同样只触 status 列，不碰 payment_status。
    op.execute("UPDATE bookings SET status='pending' WHERE status='pending_start'")
    op.execute("UPDATE bookings SET status='confirmed' WHERE status='in_progress'")
