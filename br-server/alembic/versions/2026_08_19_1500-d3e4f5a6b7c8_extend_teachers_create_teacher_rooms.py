"""extend teachers table and create teacher_rooms

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-19 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teachers', sa.Column('specialty', sa.String(50), nullable=True))
    op.add_column('teachers', sa.Column('teaching_years', sa.Integer(), server_default='0', nullable=False))
    op.add_column('teachers', sa.Column('education', sa.String(20), nullable=True))
    op.add_column('teachers', sa.Column('school', sa.String(100), nullable=True))
    op.add_column('teachers', sa.Column('status', sa.String(20), server_default='active', nullable=False))
    op.add_column('teachers', sa.Column('teaching_tags', sa.String(500), nullable=True))
    op.add_column('teachers', sa.Column('qualifications', sa.JSON(), nullable=True))

    op.create_table(
        'teacher_rooms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['room_id'], ['study_rooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('teacher_id', 'room_id', name='uq_teacher_rooms_teacher_room'),
    )
    op.create_index('ix_teacher_rooms_teacher_id', 'teacher_rooms', ['teacher_id'])
    op.create_index('ix_teacher_rooms_room_id', 'teacher_rooms', ['room_id'])


def downgrade() -> None:
    op.drop_index('ix_teacher_rooms_room_id', table_name='teacher_rooms')
    op.drop_index('ix_teacher_rooms_teacher_id', table_name='teacher_rooms')
    op.drop_table('teacher_rooms')
    op.drop_column('teachers', 'qualifications')
    op.drop_column('teachers', 'teaching_tags')
    op.drop_column('teachers', 'status')
    op.drop_column('teachers', 'school')
    op.drop_column('teachers', 'education')
    op.drop_column('teachers', 'teaching_years')
    op.drop_column('teachers', 'specialty')
