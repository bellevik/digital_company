"""phase8 agent templates and skills"""

from alembic import op
import sqlalchemy as sa

revision = "20260416_0006"
down_revision = "20260416_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("template_id", sa.String(length=100), nullable=True))
    op.add_column("agents", sa.Column("instructions", sa.Text(), nullable=True))
    op.add_column("agents", sa.Column("skill_ids", sa.JSON(), nullable=True))

    op.execute("UPDATE agents SET skill_ids = '[]'")
    op.execute(
        """
        UPDATE agents
        SET template_id = CASE role
            WHEN 'designer' THEN 'designer_product_strategist'
            WHEN 'architect' THEN 'architect_delivery_planner'
            WHEN 'developer' THEN 'developer_senior_builder'
            WHEN 'tester' THEN 'tester_regression_hunter'
            WHEN 'reviewer' THEN 'reviewer_strict_code_review'
            WHEN 'review_agent' THEN 'review_agent_release_gate'
            ELSE NULL
        END
        """
    )

    op.alter_column("agents", "skill_ids", nullable=False)


def downgrade() -> None:
    op.drop_column("agents", "skill_ids")
    op.drop_column("agents", "instructions")
    op.drop_column("agents", "template_id")
