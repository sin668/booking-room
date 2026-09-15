"""add_certification_fields_to_user_identity_verification

Revision ID: 195bfc67f12a
Revises: c7d8e9f0a1b2
Create Date: 2026-09-15 16:21:34.317634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '195bfc67f12a'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification_type column with default
    op.add_column('user_identity_verifications', sa.Column('verification_type', sa.String(20), nullable=False, server_default='real_name'))
    
    # Make existing columns nullable (they were required before)
    op.alter_column('user_identity_verifications', 'real_name', existing_type=sa.String(50), nullable=True)
    op.alter_column('user_identity_verifications', 'id_card_hash', existing_type=sa.String(64), nullable=True)
    op.alter_column('user_identity_verifications', 'id_card_masked', existing_type=sa.String(32), nullable=True)
    
    # Change status default from 'verified' to 'pending'
    op.alter_column('user_identity_verifications', 'status', existing_type=sa.String(20), server_default='pending')
    
    # Add new columns for education certification
    op.add_column('user_identity_verifications', sa.Column('school', sa.String(100), nullable=True))
    op.add_column('user_identity_verifications', sa.Column('education_level', sa.String(20), nullable=True))
    op.add_column('user_identity_verifications', sa.Column('major', sa.String(100), nullable=True))
    op.add_column('user_identity_verifications', sa.Column('graduation_year', sa.Integer(), nullable=True))
    op.add_column('user_identity_verifications', sa.Column('diploma_image_url', sa.String(512), nullable=True))
    
    # Add new columns for teacher certification
    op.add_column('user_identity_verifications', sa.Column('teacher_certificate_number', sa.String(50), nullable=True))
    op.add_column('user_identity_verifications', sa.Column('teaching_subject', sa.String(50), nullable=True))
    op.add_column('user_identity_verifications', sa.Column('certificate_image_url', sa.String(512), nullable=True))
    
    # Add rejection reason and reviewer fields
    op.add_column('user_identity_verifications', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('user_identity_verifications', sa.Column('reviewer_id', sa.UUID(), nullable=True))
    
    # Add comments using raw SQL (PostgreSQL COMMENT ON)
    op.execute("COMMENT ON COLUMN user_identity_verifications.verification_type IS '认证类型：real_name-实名认证，education-学历认证，teacher-教师资格认证'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.school IS '学校名称'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.education_level IS '学历：本科/硕士/博士'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.major IS '专业'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.graduation_year IS '毕业年份'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.diploma_image_url IS '学历证书图片URL'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.teacher_certificate_number IS '教师资格证号'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.teaching_subject IS '任教科目'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.certificate_image_url IS '教师资格证书图片URL'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.status IS '状态：pending-待审核，approved-已通过，rejected-已拒绝'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.rejection_reason IS '拒绝原因'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.reviewed_at IS '审核时间'")
    op.execute("COMMENT ON COLUMN user_identity_verifications.reviewer_id IS '审核人ID'")
    
    # Add check constraint for verification_type
    op.create_check_constraint(
        'ck_user_identity_verifications_type',
        'user_identity_verifications',
        "verification_type IN ('real_name', 'education', 'teacher')"
    )


def downgrade() -> None:
    # Remove check constraint
    op.drop_constraint('ck_user_identity_verifications_type', 'user_identity_verifications')
    
    # Drop new columns
    op.drop_column('user_identity_verifications', 'reviewer_id')
    op.drop_column('user_identity_verifications', 'rejection_reason')
    op.drop_column('user_identity_verifications', 'certificate_image_url')
    op.drop_column('user_identity_verifications', 'teaching_subject')
    op.drop_column('user_identity_verifications', 'teacher_certificate_number')
    op.drop_column('user_identity_verifications', 'diploma_image_url')
    op.drop_column('user_identity_verifications', 'graduation_year')
    op.drop_column('user_identity_verifications', 'major')
    op.drop_column('user_identity_verifications', 'education_level')
    op.drop_column('user_identity_verifications', 'school')
    op.drop_column('user_identity_verifications', 'verification_type')
    
    # Restore original column constraints
    op.alter_column('user_identity_verifications', 'real_name', existing_type=sa.String(50), nullable=False)
    op.alter_column('user_identity_verifications', 'id_card_hash', existing_type=sa.String(64), nullable=False)
    op.alter_column('user_identity_verifications', 'id_card_masked', existing_type=sa.String(32), nullable=False)
    op.alter_column('user_identity_verifications', 'status', existing_type=sa.String(20), server_default='verified')
