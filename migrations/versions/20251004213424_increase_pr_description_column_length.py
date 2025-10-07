"""increase pr description column length

Revision ID: ca5acf873f94
Revises: 930d4d1ab157
Create Date: 2025-10-04 21:34:24.395227

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ca5acf873f94'
down_revision = '930d4d1ab157'
branch_labels = None
depends_on = None


def upgrade():
    # Increase description column length to handle long PR descriptions
    op.alter_column('pull_requests', 'description',
                    existing_type=sa.VARCHAR(length=2000),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade():
    # Revert back to VARCHAR(2000) - this might truncate data
    op.alter_column('pull_requests', 'description',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(length=2000),
                    existing_nullable=True)
