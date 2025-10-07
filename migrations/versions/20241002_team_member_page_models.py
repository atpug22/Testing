"""team member page models

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2024-10-02 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # ### Enhance pull_requests table ###
    op.add_column(
        "pull_requests",
        sa.Column("labels", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "pull_requests",
        sa.Column(
            "unresolved_comments", sa.Integer(), nullable=True, server_default="0"
        ),
    )
    op.add_column(
        "pull_requests",
        sa.Column("lines_changed", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "pull_requests",
        sa.Column("additions", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "pull_requests",
        sa.Column("deletions", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "pull_requests",
        sa.Column("changed_files", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "pull_requests",
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "pull_requests",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "pull_requests",
        sa.Column("first_review_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "pull_requests",
        sa.Column("first_commit_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "pull_requests",
        sa.Column("flow_blockers", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "pull_requests",
        sa.Column("risk_flags", postgresql.ARRAY(sa.String()), nullable=True),
    )

    # Make team_id nullable (not all PRs may have team initially)
    op.alter_column("pull_requests", "team_id", nullable=True)
    op.alter_column("pull_requests", "github_url", nullable=True)

    # ### Create pr_reviewers association table ###
    op.create_table(
        "pr_reviewers",
        sa.Column("pr_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pr_id"],
            ["pull_requests.id"],
            name="fk_pr_reviewers_pr_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_pr_reviewers_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("pr_id", "user_id"),
    )

    # ### Create team_members table ###
    op.create_table(
        "team_members",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "primary_status",
            sa.String(length=50),
            nullable=False,
            server_default="balanced",
        ),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        # KPI Metrics
        sa.Column("wip_count", sa.Integer(), server_default="0"),
        sa.Column("reviews_pending_count", sa.Integer(), server_default="0"),
        sa.Column("unresolved_discussions_count", sa.Integer(), server_default="0"),
        # Velocity Metrics
        sa.Column("merged_prs_last_30_days", sa.Integer(), server_default="0"),
        sa.Column("avg_cycle_time_hours", sa.Float(), nullable=True),
        sa.Column("avg_time_to_first_review_hours", sa.Float(), nullable=True),
        # Work Focus Metrics
        sa.Column("work_focus_distribution", postgresql.JSON(), nullable=True),
        sa.Column("codebase_familiarity_percentage", sa.Float(), server_default="0"),
        # Quality Metrics
        sa.Column("rework_rate_percentage", sa.Float(), server_default="0"),
        sa.Column("revert_count", sa.Integer(), server_default="0"),
        sa.Column("churn_percentage", sa.Float(), nullable=True),
        # Collaboration Metrics
        sa.Column("review_velocity_median_hours", sa.Float(), nullable=True),
        sa.Column("collaboration_reach", sa.Integer(), server_default="0"),
        sa.Column("top_collaborators", postgresql.JSON(), nullable=True),
        # GitHub Integration
        sa.Column("github_username", sa.Unicode(length=255), nullable=True),
        sa.Column("github_user_id", sa.BigInteger(), nullable=True),
        sa.Column("github_avatar_url", sa.Unicode(length=500), nullable=True),
        sa.Column("github_profile_url", sa.Unicode(length=500), nullable=True),
        sa.Column("github_last_synced_at", sa.DateTime(timezone=True), nullable=True),
        # Jira Integration (future)
        sa.Column("jira_user_id", sa.Unicode(length=255), nullable=True),
        sa.Column("jira_email", sa.Unicode(length=255), nullable=True),
        sa.Column("jira_last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jira_metrics", postgresql.JSON(), nullable=True),
        # Confluence Integration (future)
        sa.Column("confluence_user_id", sa.Unicode(length=255), nullable=True),
        sa.Column(
            "confluence_last_synced_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("confluence_metrics", postgresql.JSON(), nullable=True),
        # Slack/Chat Integration (future)
        sa.Column("slack_user_id", sa.Unicode(length=255), nullable=True),
        sa.Column("slack_last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chat_activity_metrics", postgresql.JSON(), nullable=True),
        # Computed Insights
        sa.Column("copilot_insights", postgresql.JSON(), nullable=True),
        sa.Column("risk_factors", postgresql.JSON(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_team_members_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
        sa.UniqueConstraint("user_id"),
    )

    # ### Create events table ###
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(), nullable=False),
        sa.Column("team_member_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.Unicode(length=500), nullable=False),
        sa.Column("description", sa.Unicode(length=1000), nullable=True),
        sa.Column("pr_id", sa.BigInteger(), nullable=True),
        sa.Column("related_user_id", sa.BigInteger(), nullable=True),
        sa.Column("event_metadata", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_member_id"],
            ["team_members.id"],
            name="fk_events_team_member_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pr_id"],
            ["pull_requests.id"],
            name="fk_events_pr_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["related_user_id"],
            ["users.id"],
            name="fk_events_related_user_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    # Create index on timestamp for efficient queries
    op.create_index("idx_events_timestamp", "events", ["timestamp"])
    op.create_index("idx_events_team_member_id", "events", ["team_member_id"])


def downgrade():
    # ### Drop indexes ###
    op.drop_index("idx_events_team_member_id")
    op.drop_index("idx_events_timestamp")

    # ### Drop tables ###
    op.drop_table("events")
    op.drop_table("team_members")
    op.drop_table("pr_reviewers")

    # ### Revert pull_requests changes ###
    op.drop_column("pull_requests", "risk_flags")
    op.drop_column("pull_requests", "flow_blockers")
    op.drop_column("pull_requests", "first_commit_at")
    op.drop_column("pull_requests", "first_review_at")
    op.drop_column("pull_requests", "closed_at")
    op.drop_column("pull_requests", "merged_at")
    op.drop_column("pull_requests", "changed_files")
    op.drop_column("pull_requests", "deletions")
    op.drop_column("pull_requests", "additions")
    op.drop_column("pull_requests", "lines_changed")
    op.drop_column("pull_requests", "unresolved_comments")
    op.drop_column("pull_requests", "labels")

    op.alter_column("pull_requests", "team_id", nullable=False)
    op.alter_column("pull_requests", "github_url", nullable=False)
