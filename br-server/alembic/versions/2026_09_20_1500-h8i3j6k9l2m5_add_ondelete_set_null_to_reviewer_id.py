"""add ondelete SET NULL to reviewer_id foreign key

Revision ID: h8i3j6k9l2m5
Revises: g7h2k5m8n1p4
Create Date: 2026-09-20 15:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'h8i3j6k9l2m5'
down_revision = 'g7h2k5m8n1p4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        'user_identity_verifications_reviewer_id_fkey',
        'user_identity_verifications',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'user_identity_verifications_reviewer_id_fkey',
        'user_identity_verifications',
        'users',
        ['reviewer_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint(
        'user_identity_verifications_reviewer_id_fkey',
        'user_identity_verifications',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'user_identity_verifications_reviewer_id_fkey',
        'user_identity_verifications',
        'users',
        ['reviewer_id'],
        ['id']
    )
