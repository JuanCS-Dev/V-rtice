"""Initial schema for HITL decisions and APV reviews

Revision ID: 001
Revises:
Create Date: 2025-10-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables for HITL system."""

    # APV Reviews table
    op.create_table(
        'apv_reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('apv_code', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('cve_id', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('package_name', sa.String(100), nullable=False),
        sa.Column('package_version', sa.String(50)),
        sa.Column('patch_strategy', sa.String(50)),
        sa.Column('patch_content', sa.Text()),
        sa.Column('wargame_verdict', sa.String(50)),
        sa.Column('wargame_confidence', sa.Float()),
        sa.Column('wargame_evidence', JSONB()),
        sa.Column('confirmation_score', sa.Float()),
        sa.Column('status', sa.String(20), default='pending', index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', JSONB()),
    )

    # Decisions table
    op.create_table(
        'hitl_decisions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('apv_id', UUID(as_uuid=True), nullable=False),
        sa.Column('apv_code', sa.String(50), nullable=False, index=True),
        sa.Column('decision', sa.String(20), nullable=False, index=True),
        sa.Column('reviewer_name', sa.String(100), nullable=False),
        sa.Column('reviewer_email', sa.String(150)),
        sa.Column('action_taken', sa.String(50)),
        sa.Column('comments', sa.Text()),
        sa.Column('confidence_override', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('metadata', JSONB()),
        sa.ForeignKeyConstraint(['apv_id'], ['apv_reviews.id'], ondelete='CASCADE'),
    )

    # Indexes for performance
    op.create_index('ix_apv_reviews_status_severity', 'apv_reviews', ['status', 'severity'])
    op.create_index('ix_apv_reviews_created_at', 'apv_reviews', ['created_at'])
    op.create_index('ix_hitl_decisions_apv_id', 'hitl_decisions', ['apv_id'])
    op.create_index('ix_hitl_decisions_created_at', 'hitl_decisions', ['created_at'])

    print("✅ Initial schema created successfully")


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('hitl_decisions')
    op.drop_table('apv_reviews')
    print("✅ Schema rolled back successfully")
