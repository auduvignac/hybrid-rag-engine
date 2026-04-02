"""Chunking abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from hybrid_rag.domain.chunks import Chunk
from hybrid_rag.domain.documents import ParsedDocument


class BaseChunker(ABC):
    """Contract for chunking strategies operating on parsed documents.

    Implementations are expected to be stateless across calls so they can be
    instantiated on demand without carrying mutable state between documents.
    """

    @abstractmethod
    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Split a parsed document into retrieval-ready chunks."""
