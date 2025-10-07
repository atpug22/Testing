"""add_missing_aimodel_enum_values

Revision ID: d0628187bccb
Revises: b1f9c22936a3
Create Date: 2025-10-05 01:40:10.466983

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd0628187bccb'
down_revision = 'b1f9c22936a3'
branch_labels = None
depends_on = None


def upgrade():
    # All these values already exist in the original migration
    # azure_openai_gpt4o_mini, openai_gpt4, openai_gpt35_turbo, anthropic_claude
    # are already defined in the original migration
    pass


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the enum values in place
    pass
