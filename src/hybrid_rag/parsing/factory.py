"""Factory to create parser instances."""

from __future__ import annotations

from pathlib import Path

from hybrid_rag.parsing.base import BaseParser
from hybrid_rag.parsing.parsers import LatexParser, PdfParser
from hybrid_rag.parsing.registry import ParserRegistry


class ParserFactory:
    """Instantiate parsers from a shared registry."""

    def __init__(self, registry: ParserRegistry | None = None) -> None:
        self._registry = registry or self._build_default_registry()

    def create_parser(self, source: str | Path) -> BaseParser:
        """Return a parser instance able to handle the source."""

        parser_cls = self._registry.get_parser_class(Path(source))
        return parser_cls()

    @staticmethod
    def _build_default_registry() -> ParserRegistry:
        registry = ParserRegistry()
        registry.register(LatexParser, [".tex"])
        registry.register(PdfParser, [".pdf"])
        return registry
