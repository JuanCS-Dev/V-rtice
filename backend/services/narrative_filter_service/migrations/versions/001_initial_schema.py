"""Initial schema for narrative_filter_service.

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-10-17 12:18:00.000000

Creates 4 tables:
- semantic_representations
- strategic_patterns
- alliances
- verdicts
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Table 1: semantic_representations
    op.create_table(
        'semantic_representations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', sa.String(255), unique=True, nullable=False),
        sa.Column('source_agent_id', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('content_embedding', postgresql.ARRAY(sa.Float), nullable=False),
        sa.Column('intent_classification', sa.String(50), nullable=False),
        sa.Column('intent_confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('raw_content', sa.Text, nullable=False),
        sa.Column('provenance_chain', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for semantic_representations
    op.create_index('idx_semantic_agent_ts', 'semantic_representations', ['source_agent_id', 'timestamp'], postgresql_using='btree')
    op.create_index('idx_semantic_message_id', 'semantic_representations', ['message_id'])

    # Table 2: strategic_patterns
    op.create_table(
        'strategic_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pattern_type', sa.String(50), nullable=False),
        sa.Column('agents_involved', postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column('detection_timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('evidence_messages', postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column('mutual_information', sa.Numeric(5, 4), nullable=True),
        sa.Column('deception_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('inconsistency_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for strategic_patterns
    op.create_index('idx_patterns_type_ts', 'strategic_patterns', ['pattern_type', 'detection_timestamp'], postgresql_using='btree')

    # Table 3: alliances
    op.create_table(
        'alliances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_a', sa.String(255), nullable=False),
        sa.Column('agent_b', sa.String(255), nullable=False),
        sa.Column('strength', sa.Numeric(5, 4), nullable=False),
        sa.Column('first_detected', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('last_activity', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('interaction_count', sa.Integer, nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('agent_a', 'agent_b', name='uq_alliance_agents'),
    )

    # Table 4: verdicts
    op.create_table(
        'verdicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('agents_involved', postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column('target', sa.String(255), nullable=True),
        sa.Column('evidence_chain', postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('recommended_action', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('mitigation_command_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('color', sa.String(7), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for verdicts
    op.create_index('idx_verdicts_status_severity', 'verdicts', ['status', 'severity', 'timestamp'], postgresql_using='btree')


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_verdicts_status_severity', table_name='verdicts')
    op.drop_table('verdicts')

    op.drop_table('alliances')

    op.drop_index('idx_patterns_type_ts', table_name='strategic_patterns')
    op.drop_table('strategic_patterns')

    op.drop_index('idx_semantic_message_id', table_name='semantic_representations')
    op.drop_index('idx_semantic_agent_ts', table_name='semantic_representations')
    op.drop_table('semantic_representations')

    op.execute('DROP EXTENSION IF EXISTS vector')
