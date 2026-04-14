"""phase6 self improvement"""

from alembic import op
import sqlalchemy as sa

revision = "20260414_0004"
down_revision = "20260413_0003"
branch_labels = None
depends_on = None

self_improvement_run_status = sa.Enum(
    "running",
    "succeeded",
    "failed",
    name="self_improvement_run_status",
)
trigger_mode = sa.Enum(
    "manual",
    "scheduled",
    "seeded",
    name="self_improvement_trigger_mode",
)


def upgrade() -> None:
    op.create_table(
        "self_improvement_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("status", self_improvement_run_status, nullable=False),
        sa.Column("trigger_mode", trigger_mode, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("proposed_branch_name", sa.String(length=255), nullable=False),
        sa.Column("proposed_pr_title", sa.String(length=255), nullable=False),
        sa.Column("created_task_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_self_improvement_runs_started_at",
        "self_improvement_runs",
        ["started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_self_improvement_runs_started_at", table_name="self_improvement_runs")
    op.drop_table("self_improvement_runs")
    trigger_mode.drop(op.get_bind(), checkfirst=True)
    self_improvement_run_status.drop(op.get_bind(), checkfirst=True)
