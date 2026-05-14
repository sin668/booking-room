"""add_coupon_models

Revision ID: b3a7c9d2e4f1
Revises: 985785a787d8
Create Date: 2026-05-13 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3a7c9d2e4f1'
down_revision: Union[str, None] = '985785a787d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name

    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('discount_percent', sa.Integer(), nullable=True),
        sa.Column(
            'min_order_amount',
            sa.Numeric(precision=10, scale=2),
            server_default='0',
            nullable=False,
        ),
        sa.Column('scope', sa.String(length=30), server_default='all', nullable=False),
        sa.Column('seat_zone', sa.String(length=20), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'user_coupons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('coupon_id', sa.Integer(), sa.ForeignKey('coupons.id'), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='available', nullable=False),
        sa.Column('used_booking_id', sa.Integer(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_coupons_user_id_status', 'user_coupons', ['user_id', 'status'])
    op.create_index(op.f('ix_user_coupons_coupon_id'), 'user_coupons', ['coupon_id'])
    op.create_index(op.f('ix_user_coupons_used_booking_id'), 'user_coupons', ['used_booking_id'])

    if dialect_name == 'sqlite':
        with op.batch_alter_table('bookings', recreate='always') as batch_op:
            batch_op.add_column(
                sa.Column(
                    'original_price',
                    sa.Numeric(precision=10, scale=2),
                    server_default='0',
                    nullable=False,
                )
            )
            batch_op.add_column(
                sa.Column(
                    'discount_amount',
                    sa.Numeric(precision=10, scale=2),
                    server_default='0',
                    nullable=False,
                )
            )
            batch_op.add_column(
                sa.Column('coupon_id', sa.Integer(), sa.ForeignKey('user_coupons.id'), nullable=True)
            )
    else:
        op.add_column(
            'bookings',
            sa.Column(
                'original_price',
                sa.Numeric(precision=10, scale=2),
                server_default='0',
                nullable=False,
            ),
        )
        op.add_column(
            'bookings',
            sa.Column(
                'discount_amount',
                sa.Numeric(precision=10, scale=2),
                server_default='0',
                nullable=False,
            ),
        )
        op.add_column('bookings', sa.Column('coupon_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_bookings_coupon_id_user_coupons',
            'bookings',
            'user_coupons',
            ['coupon_id'],
            ['id'],
        )

    op.execute('UPDATE bookings SET original_price = total_price, discount_amount = 0')


def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name

    if dialect_name == 'sqlite':
        with op.batch_alter_table('bookings', recreate='always') as batch_op:
            batch_op.drop_column('coupon_id')
            batch_op.drop_column('discount_amount')
            batch_op.drop_column('original_price')
    else:
        op.drop_constraint('fk_bookings_coupon_id_user_coupons', 'bookings', type_='foreignkey')
        op.drop_column('bookings', 'coupon_id')
        op.drop_column('bookings', 'discount_amount')
        op.drop_column('bookings', 'original_price')

    op.drop_index(op.f('ix_user_coupons_used_booking_id'), table_name='user_coupons')
    op.drop_index(op.f('ix_user_coupons_coupon_id'), table_name='user_coupons')
    op.drop_index('ix_user_coupons_user_id_status', table_name='user_coupons')
    op.drop_table('user_coupons')
    op.drop_table('coupons')
