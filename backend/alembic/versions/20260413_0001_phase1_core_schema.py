"""phase1 core schema"""

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa

revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


task_status = sa.Enum("todo", "in_progress", "done", "failed", name="task_status", create_type=False)
task_type = sa.Enum("feature", "bugfix", "research", "review", "ops", name="task_type", create_type=False)
agent_role = sa.Enum(
    "designer",
    "architect",
    "developer",
    "tester",
    "reviewer",
    "review_agent",
    name="agent_role",
    create_type=False,
)
agent_status = sa.Enum("idle", "busy", "offline", name="agent_status", create_type=False)
memory_type = sa.Enum(
    "conversation",
    "decision",
    "task_result",
    "note",
    name="memory_type",
    create_type=False,
)
event_type = sa.Enum(
    "task_created",
    "task_claimed",
    "task_updated",
    "agent_created",
    "memory_created",
    name="event_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", task_type, nullable=False),
        sa.Column("status", task_status, nullable=False, server_default="todo"),
        sa.Column("assigned_agent_id", sa.UUID(), nullable=True),
        sa.Column("project_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"], unique=False)

    op.create_table(
        "agents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", agent_role, nullable=False),
        sa.Column("status", agent_status, nullable=False, server_default="idle"),
        sa.Column("current_task_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_agents_name"),
    )

    op.create_foreign_key(
        "fk_tasks_assigned_agent_id_agents",
        "tasks",
        "agents",
        ["assigned_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_agents_current_task_id_tasks",
        "agents",
        "tasks",
        ["current_task_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "memories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("type", memory_type, nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_task_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "fk_memories_source_task_id_tasks",
        "memories",
        "tasks",
        ["source_task_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("memory_id", sa.UUID(), nullable=False),
        sa.Column("vector", pgvector.sqlalchemy.Vector(dim=1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "fk_embeddings_memory_id_memories",
        "embeddings",
        "memories",
        ["memory_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "task_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=True),
        sa.Column("agent_id", sa.UUID(), nullable=True),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "fk_task_events_task_id_tasks",
        "task_events",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_task_events_agent_id_agents",
        "task_events",
        "agents",
        ["agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_task_events_task_id", "task_events", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_task_events_task_id", table_name="task_events")
    op.drop_table("task_events")
    op.drop_table("embeddings")
    op.drop_table("memories")
    op.drop_table("agents")
    op.drop_index("ix_tasks_project_id", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_table("tasks")

    bind = op.get_bind()
    event_type.drop(bind, checkfirst=True)
    memory_type.drop(bind, checkfirst=True)
    agent_status.drop(bind, checkfirst=True)
    agent_role.drop(bind, checkfirst=True)
    task_type.drop(bind, checkfirst=True)
    task_status.drop(bind, checkfirst=True)
