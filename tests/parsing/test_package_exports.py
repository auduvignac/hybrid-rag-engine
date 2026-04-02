from hybrid_rag import BibliographicReference as RootBibliographicReference
from hybrid_rag import DocumentNode as RootDocumentNode
from hybrid_rag import ParsedDocument as RootParsedDocument
from hybrid_rag import parse_document as root_parse_document
from hybrid_rag.domain import (
    BibliographicReference,
    DocumentNode,
    NodeType,
    ParsedDocument,
)
from hybrid_rag.parsing import ParserFactory, parse_document
from hybrid_rag.parsing.cli import _node_to_dict
from hybrid_rag.parsing.parsers import LatexParser, PdfParser


def test_package_exports_and_domain_helpers() -> None:
    child = DocumentNode(title="Child", level=2, node_type=NodeType.SUBSECTION)
    parent = DocumentNode(title="Parent", level=1)
    document = ParsedDocument(source_path="source.tex", document_type="latex")
    reference = BibliographicReference(title="Titre")

    parent.add_child(child)
    document.add_root_node(parent)
    document.add_bibliographic_reference("dupont2024", reference)

    assert document.root_nodes == [parent]
    assert parent.children == [child]
    assert document.bibliography == {"dupont2024": reference}
    assert RootBibliographicReference is BibliographicReference
    assert RootDocumentNode is DocumentNode
    assert RootParsedDocument is ParsedDocument
    assert root_parse_document is parse_document
    assert ParserFactory.__name__ == "ParserFactory"
    assert LatexParser.__name__ == "LatexParser"
    assert PdfParser.__name__ == "PdfParser"


def test_parsed_document_merges_bibliographic_reference_updates() -> None:
    document = ParsedDocument(source_path="source.tex", document_type="latex")
    document.add_bibliographic_reference(
        "dupont2024",
        BibliographicReference(raw_entry={"title": "Titre initial"}),
    )
    document.add_bibliographic_reference(
        "dupont2024",
        BibliographicReference(
            title="Titre",
            authors=["Jean Dupont"],
            year="2024",
            entry_type="online",
            raw_entry={"url": "https://example.org"},
        ),
    )
    document.add_bibliographic_reference(
        "dupont2024",
        BibliographicReference(year="2025"),
    )

    reference = document.bibliography["dupont2024"]
    assert reference.title == "Titre"
    assert reference.authors == ["Jean Dupont"]
    assert reference.year == "2025"
    assert reference.entry_type == "online"
    assert reference.raw_entry == {
        "title": "Titre initial",
        "url": "https://example.org",
    }


def test_cli_serializes_node_type_as_enum_value() -> None:
    node = DocumentNode(title="Parent", level=1, node_type=NodeType.SECTION)

    payload = _node_to_dict(node)

    assert payload["node_type"] == "section"
