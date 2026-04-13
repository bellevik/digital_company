"""phase2 task runs"""

from alembic import op
import sqlalchemy as sa

revision = "20260413_0002"
down_revision = "20260413_0001"
branch_labels = None
depends_on = None

task_run_status = sa.Enum(
    "running",
    "succeeded",
    "failed",
    name="task_run_status",
)


def upgrade() -> None:
    op.create_table(
        "task_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("status", task_run_status, nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("stdout", sa.Text(), nullable=False, server_default=""),
        sa.Column("stderr", sa.Text(), nullable=False, server_default=""),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("result_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_follow_up_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_runs_task_id", "task_runs", ["task_id"], unique=False)
    op.create_index("ix_task_runs_agent_id", "task_runs", ["agent_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_task_runs_agent_id", table_name="task_runs")
    op.drop_index("ix_task_runs_task_id", table_name="task_runs")
    op.drop_table("task_runs")
    task_run_status.drop(op.get_bind(), checkfirst=True)

