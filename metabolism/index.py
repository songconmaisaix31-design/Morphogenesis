"""Disposable FAISS cosine search, with lexical (not semantic) embeddings."""

from collections.abc import Callable, Sequence
from typing import Any, cast

import faiss
import numpy as np
from numpy.typing import NDArray
from sklearn.feature_extraction.text import HashingVectorizer  # type: ignore[import-untyped]

Embedding = Callable[[Sequence[str]], NDArray[np.float32]]


def lexical_embedding(texts: Sequence[str]) -> NDArray[np.float32]:
    """Stateless sklearn character ngrams; no downloads or learned semantics."""
    vectorizer = HashingVectorizer(
        n_features=2048, analyzer="char_wb", ngram_range=(2, 4),
        alternate_sign=False, norm="l2", dtype=np.float32,
    )
    return cast(NDArray[np.float32], vectorizer.transform(texts).toarray())


class CosineIndex:
    """A per-operation derived index; never a second durable source of truth."""

    def __init__(self, texts: Sequence[str], embed: Embedding) -> None:
        self.embed = embed
        self.count = len(texts)
        self.vectors = self._vectors(texts)
        self.index: Any = faiss.IndexFlatIP(self.vectors.shape[1])
        self.index.add(self.vectors)

    def _vectors(self, texts: Sequence[str]) -> NDArray[np.float32]:
        vectors = np.array(self.embed(texts), dtype=np.float32, order="C", copy=True)
        if vectors.ndim != 2 or vectors.shape[0] != len(texts) or vectors.shape[1] == 0:
            raise ValueError("embedding must return a nonempty dimension for each text")
        if not np.isfinite(vectors).all():
            raise ValueError("embedding contains nonfinite values")
        # The caller's arrays are never mutated by FAISS normalization.
        faiss.normalize_L2(vectors)
        return vectors

    def search(self, text: str) -> list[tuple[int, float]]:
        vectors = self._vectors([text])
        if vectors.shape[1] != self.vectors.shape[1]:
            raise ValueError("embedding dimension changed")
        scores, positions = self.index.search(vectors, self.count)
        return [(int(i), float(s)) for i, s in zip(positions[0], scores[0], strict=True)
                if int(i) >= 0]

    def neighbors(self, position: int) -> list[tuple[int, float]]:
        scores, positions = self.index.search(self.vectors[position:position + 1], self.count)
        return [(int(i), float(s)) for i, s in zip(positions[0], scores[0], strict=True)
                if int(i) >= 0]
