"""Chunking abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from hybrid_rag.domain.chunks import Chunk
from hybrid_rag.domain.documents import ParsedDocument


class BaseChunker(ABC):
    """Contract for chunking strategies operating on parsed documents."""

    @abstractmethod
    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Split a parsed document into retrieval-ready chunks."""

