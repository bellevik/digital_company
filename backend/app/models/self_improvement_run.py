from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import (
    SelfImprovementRunStatus,
    SelfImprovementTriggerMode,
    TimestampMixin,
    enum_values,
    uuid_primary_key,
)


class SelfImprovementRun(TimestampMixin, Base):
    __tablename__ = "self_improvement_runs"
    __table_args__ = (Index("ix_self_improvement_runs_started_at", "started_at"),)

    id: Mapped[uuid.UUID] = uuid_primary_key()
    status: Mapped[SelfImprovementRunStatus] = mapped_column(
        Enum(
            SelfImprovementRunStatus,
            name="self_improvement_run_status",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    trigger_mode: Mapped[SelfImprovementTriggerMode] = mapped_column(
        Enum(
            SelfImprovementTriggerMode,
            name="self_improvement_trigger_mode",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    proposed_pr_title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_task_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
