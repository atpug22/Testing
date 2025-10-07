"""add_new_analysis_types_to_enum

Revision ID: 742b8b72e1c2
Revises: ca5acf873f94
Create Date: 2025-10-05 01:38:32.173811

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '742b8b72e1c2'
down_revision = 'ca5acf873f94'
branch_labels = None
depends_on = None


def upgrade():
    # Add new analysis types to the existing enum
    op.execute("ALTER TYPE analysistype ADD VALUE 'pr_risk_flags'")
    op.execute("ALTER TYPE analysistype ADD VALUE 'pr_blocker_flags'")
    op.execute("ALTER TYPE analysistype ADD VALUE 'copilot_insights'")
    op.execute("ALTER TYPE analysistype ADD VALUE 'narrative_timeline'")
    op.execute("ALTER TYPE analysistype ADD VALUE 'ai_roi'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the enum values in place
    pass
