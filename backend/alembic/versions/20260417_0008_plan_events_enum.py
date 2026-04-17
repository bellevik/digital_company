"""phase9 fix event_type enum for project plans"""

from alembic import op

revision = "20260417_0008"
down_revision = "20260416_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'plan_updated'")


def downgrade() -> None:
    # PostgreSQL enums cannot reliably drop individual values in-place.
    pass
