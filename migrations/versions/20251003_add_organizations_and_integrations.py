"""add organizations and integrations

Revision ID: c3d4e5f6g7h8
Revises: a130d5806a8f
Create Date: 2025-10-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c3d4e5f6g7h8"
down_revision = "a130d5806a8f"
branch_labels = None
depends_on = None


def upgrade():
    # ### Create organizations table ###
    op.create_table(
        "organizations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=False),
        sa.Column("description", sa.Unicode(length=500), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_organizations_owner_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("uuid"),
    )

    # ### Create organization_members association table ###
    op.create_table(
        "organization_members",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_organization_members_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_members_organization_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "organization_id"),
    )

    # ### Create github_integrations table ###
    op.create_table(
        "github_integrations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("access_token", sa.Unicode(length=500), nullable=False),
        sa.Column("github_owner", sa.Unicode(length=255), nullable=True),
        sa.Column("selected_repos", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_github_integrations_organization_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    # ### Create slack_integrations table (placeholder) ###
    op.create_table(
        "slack_integrations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("webhook_url", sa.Unicode(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_slack_integrations_organization_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    # ### Create jira_integrations table (placeholder) ###
    op.create_table(
        "jira_integrations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("api_token", sa.Unicode(length=500), nullable=True),
        sa.Column("domain", sa.Unicode(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_jira_integrations_organization_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("jira_integrations")
    op.drop_table("slack_integrations")
    op.drop_table("github_integrations")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    # ### end Alembic commands ###

