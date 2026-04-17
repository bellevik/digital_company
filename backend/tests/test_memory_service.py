from __future__ import annotations

from collections.abc import Iterator, Sequence

from app.services.memory import _cosine_similarity


class AmbiguousBoolVector(Sequence[float]):
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def __getitem__(self, index: int) -> float:
        return self._values[index]

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator[float]:
        return iter(self._values)

    def __bool__(self) -> bool:
        raise ValueError("ambiguous truth value")


def test_cosine_similarity_handles_vectors_without_bool_semantics() -> None:
    left = AmbiguousBoolVector([1.0, 0.0, 0.0])
    right = AmbiguousBoolVector([1.0, 0.0, 0.0])

    score = _cosine_similarity(left, right)

    assert score == 1.0
