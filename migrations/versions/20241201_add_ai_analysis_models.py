"""Add AI analysis models

Revision ID: 20241201_add_ai_analysis_models
Revises: 20241002_add_team_and_hierarchy
Create Date: 2024-12-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241201_add_ai_analysis_models'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Create AI analysis tables
    op.create_table('ai_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_type', sa.Enum('pr_summary', 'code_review', 'risk_assessment', 'technical_debt', 'performance_analysis', 'security_analysis', 'documentation', 'custom', name='analysistype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed', 'cancelled', name='analysisstatus'), nullable=False),
        sa.Column('ai_model', sa.Enum('azure_openai_gpt4o_mini', 'openai_gpt4', 'openai_gpt35_turbo', 'anthropic_claude', name='aimodel'), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('input_text', sa.Text(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('output_text', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('prompt_template', sa.String(length=255), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('token_usage', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('pull_request_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_analyses_analysis_type'), 'ai_analyses', ['analysis_type'], unique=False)
    op.create_index(op.f('ix_ai_analyses_id'), 'ai_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_pull_request_id'), 'ai_analyses', ['pull_request_id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_status'), 'ai_analyses', ['status'], unique=False)
    op.create_index(op.f('ix_ai_analyses_team_id'), 'ai_analyses', ['team_id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_user_id'), 'ai_analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_ai_model'), 'ai_analyses', ['ai_model'], unique=False)

    op.create_table('ai_prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('analysis_type', sa.Enum('pr_summary', 'code_review', 'risk_assessment', 'technical_debt', 'performance_analysis', 'security_analysis', 'documentation', 'custom', name='analysistype'), nullable=False),
        sa.Column('ai_model', sa.Enum('azure_openai_gpt4o_mini', 'openai_gpt4', 'openai_gpt35_turbo', 'anthropic_claude', name='aimodel'), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_prompt_template', sa.Text(), nullable=False),
        sa.Column('output_schema', sa.JSON(), nullable=True),
        sa.Column('temperature', sa.Integer(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_ai_prompt_templates_analysis_type'), 'ai_prompt_templates', ['analysis_type'], unique=False)
    op.create_index(op.f('ix_ai_prompt_templates_ai_model'), 'ai_prompt_templates', ['ai_model'], unique=False)
    op.create_index(op.f('ix_ai_prompt_templates_id'), 'ai_prompt_templates', ['id'], unique=False)
    op.create_index(op.f('ix_ai_prompt_templates_name'), 'ai_prompt_templates', ['name'], unique=False)

    op.create_table('ai_usage_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ai_model', sa.Enum('azure_openai_gpt4o_mini', 'openai_gpt4', 'openai_gpt35_turbo', 'anthropic_claude', name='aimodel'), nullable=False),
        sa.Column('analysis_type', sa.Enum('pr_summary', 'code_review', 'risk_assessment', 'technical_debt', 'performance_analysis', 'security_analysis', 'documentation', 'custom', name='analysistype'), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('input_cost', sa.Integer(), nullable=False),
        sa.Column('output_cost', sa.Integer(), nullable=False),
        sa.Column('total_cost', sa.Integer(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False),
        sa.Column('success', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_usage_metrics_analysis_type'), 'ai_usage_metrics', ['analysis_type'], unique=False)
    op.create_index(op.f('ix_ai_usage_metrics_ai_model'), 'ai_usage_metrics', ['ai_model'], unique=False)
    op.create_index(op.f('ix_ai_usage_metrics_id'), 'ai_usage_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_ai_usage_metrics_team_id'), 'ai_usage_metrics', ['team_id'], unique=False)
    op.create_index(op.f('ix_ai_usage_metrics_user_id'), 'ai_usage_metrics', ['user_id'], unique=False)


def downgrade():
    # Drop AI analysis tables
    op.drop_index(op.f('ix_ai_usage_metrics_user_id'), table_name='ai_usage_metrics')
    op.drop_index(op.f('ix_ai_usage_metrics_team_id'), table_name='ai_usage_metrics')
    op.drop_index(op.f('ix_ai_usage_metrics_id'), table_name='ai_usage_metrics')
    op.drop_index(op.f('ix_ai_usage_metrics_ai_model'), table_name='ai_usage_metrics')
    op.drop_index(op.f('ix_ai_usage_metrics_analysis_type'), table_name='ai_usage_metrics')
    op.drop_table('ai_usage_metrics')

    op.drop_index(op.f('ix_ai_prompt_templates_name'), table_name='ai_prompt_templates')
    op.drop_index(op.f('ix_ai_prompt_templates_id'), table_name='ai_prompt_templates')
    op.drop_index(op.f('ix_ai_prompt_templates_ai_model'), table_name='ai_prompt_templates')
    op.drop_index(op.f('ix_ai_prompt_templates_analysis_type'), table_name='ai_prompt_templates')
    op.drop_table('ai_prompt_templates')

    op.drop_index(op.f('ix_ai_analyses_ai_model'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_user_id'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_team_id'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_status'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_pull_request_id'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_id'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_analysis_type'), table_name='ai_analyses')
    op.drop_table('ai_analyses')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS analysistype')
    op.execute('DROP TYPE IF EXISTS analysisstatus')
    op.execute('DROP TYPE IF EXISTS aimodel')

