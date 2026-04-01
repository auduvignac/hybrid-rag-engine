"""Facade used by the rest of the pipeline to parse documents."""

from __future__ import annotations

from pathlib import Path

from hybrid_rag.domain.documents import ParsedDocument
from hybrid_rag.parsing.factory import ParserFactory


class ParsingService:
    """High-level entry point for parsing source documents."""

    def __init__(self, factory: ParserFactory | None = None) -> None:
        self._factory = factory or ParserFactory()

    def parse(self, source: str | Path) -> ParsedDocument:
        """Parse a source file into a normalized document model."""

        path = Path(source)
        parser = self._factory.create_parser(path)
        return parser.parse(path)
