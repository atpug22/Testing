"""merge ai analysis and github integration

Revision ID: 930d4d1ab157
Revises: a130d5806a8f, 20241201_add_ai_analysis_models
Create Date: 2025-10-04 04:55:03.068369

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '930d4d1ab157'
down_revision = ('a130d5806a8f', '20241201_add_ai_analysis_models')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
