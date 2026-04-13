from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.embedding import Embedding
from app.models.memory import Memory
from app.models.task import Task
from app.schemas.memory_search import MemorySearchResult


class MemoryService:
    def __init__(self, *, db: Session, settings: Settings):
        self._db = db
        self._settings = settings

    def create_memory(
        self,
        *,
        memory_type,
        summary: str,
        content: str,
        source_task_id,
    ) -> Memory:
        memory = Memory(
            type=memory_type,
            summary=summary,
            content=content,
            source_task_id=source_task_id,
        )
        self._db.add(memory)
        self._db.flush()

        vector = self._embed_text(f"{summary}\n{content}")
        self._db.add(Embedding(memory_id=memory.id, vector=vector))
        self._db.flush()
        self._db.refresh(memory)
        return memory

    def search_memories(
        self,
        *,
        query: str,
        limit: int,
        project_id: str | None = None,
        source_task_id=None,
        strategy: str = "hybrid",
    ) -> list[MemorySearchResult]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        memories = self._candidate_memories(project_id=project_id, source_task_id=source_task_id)
        query_vector = self._embed_text(normalized_query)
        results: list[MemorySearchResult] = []

        for memory in memories:
            keyword_score = _keyword_score(normalized_query, memory.summary, memory.content)
            vector_score = _cosine_similarity(
                query_vector,
                memory.embeddings[0].vector if memory.embeddings else self._embed_text(f"{memory.summary}\n{memory.content}"),
            )
            combined_score = _combine_scores(
                strategy=strategy,
                keyword_score=keyword_score,
                vector_score=vector_score,
            )
            if combined_score <= 0:
                continue
            results.append(
                MemorySearchResult(
                    memory_id=memory.id,
                    type=memory.type,
                    summary=memory.summary,
                    content=memory.content,
                    source_task_id=memory.source_task_id,
                    created_at=memory.created_at,
                    keyword_score=round(keyword_score, 6),
                    vector_score=round(vector_score, 6),
                    combined_score=round(combined_score, 6),
                )
            )

        results.sort(key=lambda item: (item.combined_score, item.created_at), reverse=True)
        return results[:limit]

    def _candidate_memories(self, *, project_id: str | None, source_task_id) -> list[Memory]:
        query: Select[tuple[Memory]] = select(Memory).order_by(Memory.created_at.desc())

        if project_id is not None:
            query = (
                select(Memory)
                .join(Task, Memory.source_task_id == Task.id, isouter=True)
                .where((Task.project_id == project_id) | (Memory.source_task_id.is_(None)))
                .order_by(Memory.created_at.desc())
            )

        if source_task_id is not None:
            query = query.where((Memory.source_task_id == source_task_id) | (Memory.source_task_id.is_(None)))

        query = query.limit(self._settings.memory_search_candidate_limit)
        return list(self._db.scalars(query).unique().all())

    def _embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        seed_material = text.encode("utf-8")
        counter = 0

        while len(values) < self._settings.memory_embedding_dimensions:
            block = hashlib.sha256(seed_material + digest + counter.to_bytes(4, "big")).digest()
            for index in range(0, len(block), 2):
                if len(values) >= self._settings.memory_embedding_dimensions:
                    break
                chunk = int.from_bytes(block[index : index + 2], "big", signed=False)
                values.append((chunk / 65535.0) * 2.0 - 1.0)
            counter += 1

        return values


def _keyword_score(query: str, summary: str, content: str) -> float:
    haystack_summary = summary.lower()
    haystack_content = content.lower()
    terms = [term for term in query.lower().split() if term]
    if not terms:
        return 0.0

    score = 0.0
    for term in terms:
        if term in haystack_summary:
            score += 2.0
        if term in haystack_content:
            score += 1.0
    return score / max(len(terms) * 3.0, 1.0)


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(dot_product / (left_norm * right_norm), 0.0)


def _combine_scores(*, strategy: str, keyword_score: float, vector_score: float) -> float:
    if strategy == "keyword":
        return keyword_score
    if strategy == "vector":
        return vector_score
    return (keyword_score * 0.45) + (vector_score * 0.55)
