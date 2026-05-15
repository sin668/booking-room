"""add_cities_table_and_room_city_id

Revision ID: 7c9d2e4f6a1b
Revises: f836feddafc6
Create Date: 2026-05-15 17:15:00.000000

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c9d2e4f6a1b"
down_revision: Union[str, None] = "f836feddafc6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    with op.batch_alter_table("study_rooms") as batch_op:
        batch_op.add_column(sa.Column("city_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_study_rooms_city_id_cities", "cities", ["city_id"], ["id"]
        )

    now = datetime.now()
    cities_table = sa.table(
        "cities",
        sa.column("name", sa.String),
        sa.column("province", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("status", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    op.bulk_insert(
        cities_table,
        [
            {
                "name": "茂名市",
                "province": "广东省",
                "sort_order": 1,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "广州市",
                "province": "广东省",
                "sort_order": 2,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "深圳市",
                "province": "广东省",
                "sort_order": 3,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "东莞市",
                "province": "广东省",
                "sort_order": 4,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "佛山市",
                "province": "广东省",
                "sort_order": 5,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "珠海市",
                "province": "广东省",
                "sort_order": 6,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
        ],
    )

    op.execute(
        "UPDATE study_rooms "
        "SET city_id = (SELECT id FROM cities WHERE name = '茂名市') "
        "WHERE city_id IS NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table("study_rooms") as batch_op:
        batch_op.drop_constraint("fk_study_rooms_city_id_cities", type_="foreignkey")
        batch_op.drop_column("city_id")

    op.drop_table("cities")
