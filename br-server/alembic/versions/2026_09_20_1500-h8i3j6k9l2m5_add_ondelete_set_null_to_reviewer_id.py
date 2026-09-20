"""add ondelete SET NULL to reviewer_id foreign key

Revision ID: h8i3j6k9l2m5
Revises: g7h2k5m8n1p4
Create Date: 2026-09-20 15:00:00.000000

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'h8i3j6k9l2m5'
down_revision = 'g7h2k5m8n1p4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Find the actual constraint name
    result = conn.execute(text("""
        SELECT con.conname
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
          AND rel.relname = 'user_identity_verifications'
          AND con.contype = 'f'
          AND con.conname LIKE '%reviewer_id%'
    """))
    row = result.fetchone()
    if row:
        constraint_name = row[0]
        op.drop_constraint(constraint_name, 'user_identity_verifications', type_='foreignkey')
    op.create_foreign_key(
        'user_identity_verifications_reviewer_id_fkey',
        'user_identity_verifications',
        'users',
        ['reviewer_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(text("""
        SELECT con.conname
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE nsp.nspname = 'public'
          AND rel.relname = 'user_identity_verifications'
          AND con.contype = 'f'
          AND con.conname LIKE '%reviewer_id%'
    """))
    row = result.fetchone()
    if row:
        constraint_name = row[0]
        op.drop_constraint(constraint_name, 'user_identity_verifications', type_='foreignkey')
    op.create_foreign_key(
        'user_identity_verifications_reviewer_id_fkey',
        'user_identity_verifications',
        'users',
        ['reviewer_id'],
        ['id']
    )
