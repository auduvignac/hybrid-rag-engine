"""High-level chunking entry points."""

from __future__ import annotations

from hybrid_rag.chunking.base import BaseChunker
from hybrid_rag.chunking.strategies import DocumentNodeChunker
from hybrid_rag.domain.chunks import Chunk
from hybrid_rag.domain.documents import ParsedDocument

_DEFAULT_CHUNKER = DocumentNodeChunker()


def chunk_document(
    document: ParsedDocument, chunker: BaseChunker | None = None
) -> list[Chunk]:
    """Chunk a parsed document into retrieval-oriented units."""

    active_chunker = chunker or _DEFAULT_CHUNKER
    return active_chunker.chunk(document)

