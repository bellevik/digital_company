from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import MemoryType, TimestampMixin, enum_values, uuid_primary_key


class Memory(TimestampMixin, Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType, name="memory_type", values_callable=enum_values),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    source_task: Mapped["Task | None"] = relationship("Task", back_populates="memories")
    embeddings: Mapped[list["Embedding"]] = relationship(
        "Embedding",
        back_populates="memory",
        cascade="all, delete-orphan",
    )
