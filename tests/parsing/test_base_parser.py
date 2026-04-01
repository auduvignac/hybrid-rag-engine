from pathlib import Path

import pytest

from hybrid_rag.domain.documents import ParsedDocument
from hybrid_rag.parsing.base import BaseParser
from hybrid_rag.parsing.factory import ParserFactory
from hybrid_rag.parsing.registry import ParserRegistry
from hybrid_rag.parsing.service import ParsingService


class RejectingParser(BaseParser):
    def can_handle(self, source: Path) -> bool:
        return False

    def _load(self, source: Path) -> str:
        return ""

    def _extract_structure(self, content: str, source: Path) -> ParsedDocument:
        return ParsedDocument(source_path=str(source), document_type="dummy")


class RecordingParser(BaseParser):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def can_handle(self, source: Path) -> bool:
        self.calls.append("can_handle")
        return source.suffix == ".dummy"

    def _load(self, source: Path) -> str:
        self.calls.append("load")
        return "payload"

    def _extract_structure(self, content: str, source: Path) -> ParsedDocument:
        self.calls.append(f"extract:{content}")
        return ParsedDocument(source_path=str(source), document_type="dummy")


class FallbackParser(BaseParser):
    def can_handle(self, source: Path) -> bool:
        return source.name.startswith("CR_")

    def _load(self, source: Path) -> str:
        return ""

    def _extract_structure(self, content: str, source: Path) -> ParsedDocument:
        return ParsedDocument(
            source_path=str(source), document_type="fallback"
        )


def test_base_parser_raises_value_error_when_source_is_not_supported() -> None:
    parser = RejectingParser()
    source = Path("unsupported.md")

    with pytest.raises(
        ValueError,
        match=r"RejectingParser cannot handle source 'unsupported\.md'\.",
    ):
        parser.parse(source)


def test_base_parser_template_method_uses_default_normalize_and_post_process() -> (
    None
):
    parser = RecordingParser()

    document = parser.parse(Path("example.dummy"))

    assert document.document_type == "dummy"
    assert parser.calls == ["can_handle", "load", "extract:payload"]


def test_registry_resolves_by_extension_and_can_handle_fallback() -> None:
    registry = ParserRegistry()
    registry.register(RecordingParser, ["dummy"])
    registry.register(FallbackParser, [".fallback"])
    registry.register(FallbackParser, [".other"])

    assert registry.get_parser_class(Path("example.dummy")) is RecordingParser
    assert registry.get_parser_class(Path("CR_2026.custom")) is FallbackParser
    assert registry.get_parser_class(Path("example.other")) is FallbackParser


def test_registry_raises_clear_errors_for_invalid_registration_and_unknown_source() -> (
    None
):
    registry = ParserRegistry()

    with pytest.raises(
        ValueError,
        match=r"No extensions provided for parser 'RecordingParser'\.",
    ):
        registry.register(RecordingParser, [])

    with pytest.raises(
        LookupError,
        match=r"No parser registered for source 'notes\.md' \(extension '\.md'\)\.",
    ):
        registry.get_parser_class(Path("notes.md"))


def test_factory_and_service_can_use_custom_registry(tmp_path: Path) -> None:
    source = tmp_path / "example.dummy"
    source.write_text("payload", encoding="utf-8")
    registry = ParserRegistry()
    registry.register(RecordingParser, [".dummy"])

    factory = ParserFactory(registry=registry)
    service = ParsingService(factory=factory)

    parser = factory.create_parser(source)
    document = service.parse(source)

    assert isinstance(parser, RecordingParser)
    assert document.document_type == "dummy"


def test_default_factory_and_service_support_tex_and_reject_unknown_sources() -> (
    None
):
    factory = ParserFactory()

    assert (
        factory.create_parser(Path("sample.tex")).__class__.__name__
        == "LatexParser"
    )
    assert (
        factory.create_parser(Path("sample.pdf")).__class__.__name__
        == "PdfParser"
    )
    assert (
        ParsingService()
        .parse(Path("tests/parsing/fixtures/sample_cr.tex"))
        .document_type
        == "latex"
    )

    with pytest.raises(LookupError, match="No parser registered"):
        factory.create_parser(Path("notes.md"))
