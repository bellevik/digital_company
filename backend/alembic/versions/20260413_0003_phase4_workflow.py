"""phase4 workflow"""

from alembic import op
import sqlalchemy as sa

revision = "20260413_0003"
down_revision = "20260413_0002"
branch_labels = None
depends_on = None

approval_status = sa.Enum(
    "not_required",
    "pending_approval",
    "approved",
    "changes_requested",
    name="approval_status",
)
review_decision_type = sa.Enum(
    "approved",
    "changes_requested",
    name="review_decision_type",
)


def upgrade() -> None:
    op.create_table(
        "task_workflows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("latest_task_run_id", sa.UUID(), nullable=True),
        sa.Column("approval_status", approval_status, nullable=False, server_default="not_required"),
        sa.Column("branch_name", sa.String(length=255), nullable=True),
        sa.Column("submission_notes", sa.Text(), nullable=True),
        sa.Column("submitted_for_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["latest_task_run_id"], ["task_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("ix_task_workflows_approval_status", "task_workflows", ["approval_status"], unique=False)

    op.create_table(
        "review_decisions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("task_workflow_id", sa.UUID(), nullable=False),
        sa.Column("task_run_id", sa.UUID(), nullable=True),
        sa.Column("reviewer_name", sa.String(length=100), nullable=False),
        sa.Column("decision", review_decision_type, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_workflow_id"], ["task_workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_run_id"], ["task_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_decisions_task_id", "review_decisions", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_review_decisions_task_id", table_name="review_decisions")
    op.drop_table("review_decisions")
    op.drop_index("ix_task_workflows_approval_status", table_name="task_workflows")
    op.drop_table("task_workflows")
    review_decision_type.drop(op.get_bind(), checkfirst=True)
    approval_status.drop(op.get_bind(), checkfirst=True)
