"""phase9 project plans"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260416_0007"
down_revision = "20260416_0006"
branch_labels = None
depends_on = None

project_plan_status = sa.Enum(
    "draft",
    "pending_approval",
    "changes_requested",
    "approved",
    "completed",
    name="project_plan_status",
)
project_plan_task_status = sa.Enum(
    "proposed",
    "queued",
    "done",
    "failed",
    "cancelled",
    name="project_plan_task_status",
)
project_plan_status_no_create = postgresql.ENUM(
    "draft",
    "pending_approval",
    "changes_requested",
    "approved",
    "completed",
    name="project_plan_status",
    create_type=False,
)
project_plan_task_status_no_create = postgresql.ENUM(
    "proposed",
    "queued",
    "done",
    "failed",
    "cancelled",
    name="project_plan_task_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute("ALTER TYPE task_type ADD VALUE IF NOT EXISTS 'idea'")
    op.execute("ALTER TYPE agent_role ADD VALUE IF NOT EXISTS 'planner'")
    project_plan_status.create(op.get_bind(), checkfirst=True)
    project_plan_task_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "project_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.String(length=100), nullable=False),
        sa.Column("planning_task_id", sa.Uuid(), nullable=True),
        sa.Column("idea_title", sa.String(length=255), nullable=False),
        sa.Column("idea_description", sa.Text(), nullable=False),
        sa.Column("planner_summary", sa.Text(), nullable=True),
        sa.Column("status", project_plan_status_no_create, nullable=False, server_default="draft"),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("max_total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_task_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "project_plan_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_plan_id", sa.Uuid(), nullable=False),
        sa.Column("parent_plan_task_id", sa.Uuid(), nullable=True),
        sa.Column("source_task_id", sa.Uuid(), nullable=True),
        sa.Column("created_task_id", sa.Uuid(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", postgresql.ENUM(name="task_type", create_type=False), nullable=False),
        sa.Column("status", project_plan_task_status_no_create, nullable=False, server_default="proposed"),
        sa.Column("spawn_budget", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_plan_id"], ["project_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("tasks", sa.Column("plan_id", sa.Uuid(), nullable=True))
    op.add_column("tasks", sa.Column("plan_item_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "plan_item_id")
    op.drop_column("tasks", "plan_id")
    op.drop_table("project_plan_tasks")
    op.drop_table("project_plans")
    sa.Enum(name="project_plan_task_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="project_plan_status").drop(op.get_bind(), checkfirst=True)
