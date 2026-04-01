"""Registry for parser classes."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from hybrid_rag.parsing.base import BaseParser

ParserType = type[BaseParser]


class ParserRegistry:
    """Store parser classes and resolve them from file extensions."""

    def __init__(self) -> None:
        self._parsers_by_extension: dict[str, ParserType] = {}
        self._parser_classes: list[ParserType] = []

    def register(
        self, parser_cls: ParserType, extensions: Iterable[str]
    ) -> None:
        """Register a parser class for one or more file extensions."""

        normalized_extensions = [
            self._normalize_extension(ext) for ext in extensions
        ]
        if not normalized_extensions:
            raise ValueError(
                f"No extensions provided for parser '{parser_cls.__name__}'."
            )

        for extension in normalized_extensions:
            self._parsers_by_extension[extension] = parser_cls

        if parser_cls not in self._parser_classes:
            self._parser_classes.append(parser_cls)

    def get_parser_class(self, source: Path) -> ParserType:
        """Resolve a parser class for a source path."""

        source = Path(source)
        parser_cls = self._parsers_by_extension.get(source.suffix.lower())
        if parser_cls is not None:
            return parser_cls

        for candidate in self._parser_classes:
            if candidate.can_handle(source):
                return candidate

        raise LookupError(
            f"No parser registered for source '{source}' (extension '{source.suffix}')."
        )

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        return extension if extension.startswith(".") else f".{extension}"
