from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_primary_key
from app.models.types import EmbeddingVector


class Embedding(TimestampMixin, Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    memory_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
    )
    vector: Mapped[list[float]] = mapped_column(EmbeddingVector(), nullable=False)

    memory: Mapped["Memory"] = relationship("Memory", back_populates="embeddings")
