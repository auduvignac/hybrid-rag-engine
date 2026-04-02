from pathlib import Path

import pytest

from hybrid_rag.parsing.parsers import PdfParser


def test_pdf_parser_can_handle_pdf_sources() -> None:
    parser = PdfParser()

    assert parser.can_handle(Path("report.pdf")) is True
    assert parser.can_handle(Path("report.tex")) is False


def test_pdf_parser_placeholder_methods_raise_user_level_error(
    tmp_path: Path,
) -> None:
    parser = PdfParser()
    source = tmp_path / "report.pdf"
    source.write_text("placeholder", encoding="utf-8")

    with pytest.raises(ValueError, match="PDF parsing is not supported yet."):
        parser._load(source)

    with pytest.raises(ValueError, match="PDF parsing is not supported yet."):
        parser._extract_structure("content", source)

    with pytest.raises(ValueError, match="PDF parsing is not supported yet."):
        parser.parse(source)
