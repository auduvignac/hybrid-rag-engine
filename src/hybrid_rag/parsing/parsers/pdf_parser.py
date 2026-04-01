"""PDF parser placeholder."""

from __future__ import annotations

from pathlib import Path

from hybrid_rag.domain.documents import ParsedDocument
from hybrid_rag.parsing.base import BaseParser


class PdfParser(BaseParser):
    """Placeholder parser for future PDF support."""

    def can_handle(self, source: Path) -> bool:
        return Path(source).suffix.lower() == ".pdf"

    def _load(self, source: Path) -> str:
        raise NotImplementedError("PDF parsing is not implemented yet.")

    def _extract_structure(self, content: str, source: Path) -> ParsedDocument:
        raise NotImplementedError("PDF parsing is not implemented yet.")
