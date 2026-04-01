from pathlib import Path

from hybrid_rag.domain.documents import DocumentNode, ParsedDocument
from hybrid_rag.domain.enums import NodeType
from hybrid_rag.parsing.parsers import LatexParser


def test_latex_parser_builds_expected_hierarchy() -> None:
    fixture = Path("tests/parsing/fixtures/sample_cr.tex")

    parser = LatexParser()
    document = parser.parse(fixture)

    assert isinstance(document, ParsedDocument)
    assert document.document_type == "latex"
    assert document.title == "Compte Rendu Projet"
    assert len(document.root_nodes) == 2
    assert parser.can_handle(fixture) is True
    assert parser.can_handle(Path("sample.pdf")) is False

    section = document.root_nodes[0]
    assert section.title == "Introduction"
    assert section.node_type == NodeType.SECTION
    assert "prototype" in section.content
    assert "commentaire" not in section.content.lower()
    assert section.metadata["source_file"] == "sample_cr.tex"
    assert section.metadata["sectioning_level"] == 2
    assert section.metadata["label_value"] == "sec:intro"

    subsection = section.children[0]
    assert subsection.title == "Contexte"
    assert subsection.node_type == NodeType.SUBSECTION
    assert "Important pour le pipeline." in subsection.content

    subsubsection = subsection.children[0]
    assert subsubsection.title == "Details"
    assert subsubsection.node_type == NodeType.SUBSUBSECTION
    assert (
        "Les commandes simples ne doivent pas casser le texte."
        in subsubsection.content
    )

    second_section = document.root_nodes[1]
    assert second_section.title == "Elements complémentaires"
    assert second_section.metadata["label_value"] == "sec:compl"
    assert second_section.children[0].title == "Details"


def test_latex_parser_falls_back_to_document_node_without_sections(
    tmp_path: Path,
) -> None:
    source = tmp_path / "CR_note.tex"
    source.write_text(
        "Texte libre avec \\textbf{mise en avant}.", encoding="utf-8"
    )

    document = LatexParser().parse(source)

    assert len(document.root_nodes) == 1
    root = document.root_nodes[0]
    assert root.node_type == NodeType.DOCUMENT
    assert root.level == 0
    assert "mise en avant" in root.content


def test_latex_parser_helpers_cover_post_process_and_normalization() -> None:
    parser = LatexParser()
    root_node = DocumentNode(
        title="Titre principal", level=1, node_type=NodeType.SECTION
    )
    document = ParsedDocument(
        source_path="tests/parsing/fixtures/sample_cr.tex",
        document_type="latex",
        title=None,
        root_nodes=[root_node],
    )

    parser._post_process(document)

    assert root_node.title == "Titre principal"
    assert document.title == "Titre principal"
    assert (
        parser._infer_document_title("contenu", Path("fallback_title.tex"))
        == "fallback_title"
    )
    assert (
        parser._strip_comments(r"100\% conserve % commentaire supprime")
        == r"100\% conserve "
    )
    assert (
        parser._clean_inline_text(
            r"\noindent \textbf{Texte} \emph{important} \footcite{source2025} \label{sec:test} \unknown{valeur}"
        )
        == "Texte important valeur"
    )
    assert parser._extract_citations(r"\footcite{source2025, other2024}\footcite{source2025}") == [
        "source2025",
        "other2024",
    ]
    assert (
        parser._clean_text(
            "\\begin{itemize}\n\\item Premier point\n\\item Deuxieme point\n\\end{itemize}"
        )
        == "- Premier point\n- Deuxieme point"
    )
    assert parser._clean_text("Ligne 1\n\n\n Ligne 2") == "Ligne 1\n\n Ligne 2"


def test_latex_parser_extracts_citations_into_metadata_and_removes_them_from_content(
    tmp_path: Path,
) -> None:
    source = tmp_path / "CR_citations.tex"
    source.write_text(
        "\\section{Introduction}\n"
        "Texte avec citation\\footcite{dupont2024} et citations multiples"
        "\\footcite{martin2023, dupont2024}.\n",
        encoding="utf-8",
    )

    document = LatexParser().parse(source)

    section = document.root_nodes[0]
    assert section.metadata["citations"] == ["dupont2024", "martin2023"]
    assert "footcite" not in section.content
    assert "dupont2024" not in section.content
    assert "martin2023" not in section.content
