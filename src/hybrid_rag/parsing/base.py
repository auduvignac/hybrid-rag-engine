"""Common abstractions for document parsers."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from hybrid_rag.domain.documents import ParsedDocument

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Template method for document parsing pipelines."""

    def parse(self, source: Path) -> ParsedDocument:
        """Run the full parsing pipeline for a given source."""

        path = Path(source)
        if not self.can_handle(path):
            raise ValueError(
                f"{self.__class__.__name__} cannot handle source '{path}'."
            )

        raw_content = self._load(path)
        normalized_content = self._normalize(raw_content)
        document = self._extract_structure(normalized_content, path)
        self._post_process(document)
        return document

    @classmethod
    @abstractmethod
    def can_handle(cls, source: Path) -> bool:
        """Return whether this parser supports the given source."""

    @abstractmethod
    def _load(self, source: Path) -> str:
        """Load the raw textual content from a source."""

    def _normalize(self, content: str) -> str:
        """Normalize raw content before structure extraction."""

        return content

    @abstractmethod
    def _extract_structure(self, content: str, source: Path) -> ParsedDocument:
        """Build a normalized document tree from normalized text."""

    def _post_process(self, document: ParsedDocument) -> None:
        """Apply lightweight in-place cleanup after extraction."""
