"""fix_enum_values_and_add_missing_status

Revision ID: b1f9c22936a3
Revises: 742b8b72e1c2
Create Date: 2025-10-05 01:39:05.226739

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b1f9c22936a3'
down_revision = '742b8b72e1c2'
branch_labels = None
depends_on = None


def upgrade():
    # These values already exist in the original migration
    # pr_summary is already in analysistype
    # in_progress is already in analysisstatus
    pass


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the enum values in place
    pass
