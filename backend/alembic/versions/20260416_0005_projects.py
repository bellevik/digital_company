"""phase7 projects"""

from alembic import op
import sqlalchemy as sa

revision = "20260416_0005"
down_revision = "20260414_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.execute(
        """
        INSERT INTO projects (id, name, description, created_at, updated_at)
        SELECT DISTINCT project_id, project_id, 'Imported from existing task data.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM tasks
        WHERE project_id IS NOT NULL
        """
    )

    op.create_foreign_key(
        "fk_tasks_project_id_projects",
        "tasks",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tasks_project_id_projects", "tasks", type_="foreignkey")
    op.drop_table("projects")
