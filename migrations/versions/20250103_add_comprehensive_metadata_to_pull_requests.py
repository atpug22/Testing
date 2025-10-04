"""Add comprehensive metadata fields to pull_requests

Revision ID: add_comprehensive_metadata
Revises: 20251003_add_organizations_and_integrations
Create Date: 2025-01-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_comprehensive_metadata'
down_revision = '20251003_add_organizations_and_integrations'
branch_labels = None
depends_on = None


def upgrade():
    # Add comprehensive metadata fields to pull_requests table
    op.add_column('pull_requests', sa.Column('pr_metadata', sa.JSON(), nullable=True))
    op.add_column('pull_requests', sa.Column('cicd_metadata', sa.JSON(), nullable=True))
    op.add_column('pull_requests', sa.Column('time_cycle_metadata', sa.JSON(), nullable=True))
    op.add_column('pull_requests', sa.Column('reviewers_metadata', sa.JSON(), nullable=True))
    op.add_column('pull_requests', sa.Column('file_changes_metadata', sa.JSON(), nullable=True))
    op.add_column('pull_requests', sa.Column('linked_issues_metadata', sa.JSON(), nullable=True))
    op.add_column('pull_requests', sa.Column('git_blame_metadata', sa.JSON(), nullable=True))
    op.add_column('pull_requests', sa.Column('repository_info', sa.JSON(), nullable=True))


def downgrade():
    # Remove comprehensive metadata fields from pull_requests table
    op.drop_column('pull_requests', 'repository_info')
    op.drop_column('pull_requests', 'git_blame_metadata')
    op.drop_column('pull_requests', 'linked_issues_metadata')
    op.drop_column('pull_requests', 'file_changes_metadata')
    op.drop_column('pull_requests', 'reviewers_metadata')
    op.drop_column('pull_requests', 'time_cycle_metadata')
    op.drop_column('pull_requests', 'cicd_metadata')
    op.drop_column('pull_requests', 'pr_metadata')
