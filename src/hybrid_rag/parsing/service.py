"""High-level entry point helpers for document parsing."""

from __future__ import annotations

from pathlib import Path

from hybrid_rag.domain.documents import ParsedDocument
from hybrid_rag.parsing.factory import ParserFactory

_DEFAULT_FACTORY = ParserFactory()


def parse_document(
    source: str | Path, factory: ParserFactory | None = None
) -> ParsedDocument:
    """Parse a source file into a normalized document model."""

    path = Path(source)
    parser_factory = factory or _DEFAULT_FACTORY
    parser = parser_factory.create_parser(path)
    return parser.parse(path)
