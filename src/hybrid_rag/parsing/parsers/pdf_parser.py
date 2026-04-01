"""PDF parser placeholder."""

from __future__ import annotations

from pathlib import Path

from hybrid_rag.domain.documents import ParsedDocument
from hybrid_rag.parsing.base import BaseParser


class PdfParser(BaseParser):
    """Placeholder parser for future PDF support.

    Any attempt to parse a PDF currently raises a user-level error so callers
    can surface a friendly message or choose an alternative input path.
    """

    _UNSUPPORTED_MESSAGE = (
        "PDF parsing is not supported yet. "
        "Please convert the PDF to a supported text format before processing."
    )

    @classmethod
    def can_handle(cls, source: Path) -> bool:
        return Path(source).suffix.lower() == ".pdf"

    def _load(self, source: Path) -> str:
        raise ValueError(self._UNSUPPORTED_MESSAGE)

    def _extract_structure(self, content: str, source: Path) -> ParsedDocument:
        raise ValueError(self._UNSUPPORTED_MESSAGE)
