from hybrid_rag import DocumentNode as RootDocumentNode
from hybrid_rag import ParsedDocument as RootParsedDocument
from hybrid_rag import ParsingService as RootParsingService
from hybrid_rag.domain import DocumentNode, NodeType, ParsedDocument
from hybrid_rag.parsing import ParserFactory, ParsingService
from hybrid_rag.parsing.parsers import LatexParser, PdfParser


def test_package_exports_and_domain_helpers() -> None:
    child = DocumentNode(title="Child", level=2, node_type=NodeType.SUBSECTION)
    parent = DocumentNode(title="Parent", level=1)
    document = ParsedDocument(source_path="source.tex", document_type="latex")

    parent.add_child(child)
    document.add_root_node(parent)

    assert document.root_nodes == [parent]
    assert parent.children == [child]
    assert RootDocumentNode is DocumentNode
    assert RootParsedDocument is ParsedDocument
    assert RootParsingService is ParsingService
    assert ParserFactory.__name__ == "ParserFactory"
    assert LatexParser.__name__ == "LatexParser"
    assert PdfParser.__name__ == "PdfParser"
