"""Core package for the hybrid RAG engine."""

from hybrid_rag.domain.documents import (
    BibliographicReference,
    DocumentNode,
    ParsedDocument,
)
from hybrid_rag.domain.chunks import Chunk
from hybrid_rag.parsing.service import parse_document

__all__ = [
    "BibliographicReference",
    "Chunk",
    "DocumentNode",
    "ParsedDocument",
    "parse_document",
]
