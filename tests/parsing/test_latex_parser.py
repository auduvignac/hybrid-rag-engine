from pathlib import Path

import pytest

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
    assert parser.can_handle(Path("REPORT.TEX")) is True
    assert parser.can_handle(Path("sample.pdf")) is False

    section = document.root_nodes[0]
    assert section.title == "Introduction"
    assert section.node_type == NodeType.SECTION
    assert "prototype" in section.content
    assert "commentaire" not in section.content.lower()
    assert section.metadata["source_file"] == "sample_cr.tex"
    assert section.metadata["sectioning_level"] == 2
    assert section.metadata["label_value"] == "sec:intro"
    assert section.metadata["citations"] == []
    assert section.metadata["citation_links"] == []
    assert document.bibliography == {}

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
    assert parser._extract_citation_links(
        current_content=(
            "Premiere phrase avec source\\footcite{source2025}. "
            "Deuxieme phrase sans citation."
        ),
        cleaned_content="Premiere phrase avec source. Deuxieme phrase sans citation.",
    ) == [
        {
            "start": 0,
            "end": 28,
            "text": "Premiere phrase avec source.",
            "citations": ["source2025"],
        }
    ]
    assert parser._extract_citation_segments(
        "\\begin{itemize}\n"
        "\\item Premier item\\footcite{source2025}\n"
        "\\item Deuxieme item\\footcite{other2024, source2025}\n"
        "\\end{itemize}"
    ) == [
        "Premier item\\footcite{source2025}",
        "Deuxieme item\\footcite{other2024, source2025}",
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
    assert set(document.bibliography) == {"dupont2024", "martin2023"}
    assert document.bibliography["dupont2024"].title is None
    assert section.metadata["citation_links"] == [
        {
            "start": 0,
            "end": len("Texte avec citation et citations multiples."),
            "text": "Texte avec citation et citations multiples.",
            "citations": ["dupont2024", "martin2023"],
        }
    ]
    assert "footcite" not in section.content
    assert "dupont2024" not in section.content
    assert "martin2023" not in section.content


def test_latex_parser_extracts_bibliography_paths_and_resolves_entries() -> None:
    fixture = Path("tests/parsing/fixtures/CR.tex")

    document = LatexParser().parse(fixture)

    expected_paths = [
        str((fixture.parent / "bibliographies/articles.bib").resolve()),
        str((fixture.parent / "bibliographies/livres.bib").resolve()),
        str((fixture.parent / "bibliographies/online.bib").resolve()),
        str((fixture.parent / "bibliographies/rapports.bib").resolve()),
    ]

    assert "lefigaro2025munichdrones" in document.bibliography
    assert "livreblanc2013defense" in document.bibliography
    assert document.bibliography["lefigaro2025munichdrones"].title is not None
    assert document.bibliography["lefigaro2025munichdrones"].entry_type == "online"
    assert (
        document.bibliography["lefigaro2025munichdrones"].raw_entry["journal"]
        == "Le Figaro"
    )
    assert (
        document.bibliography["roblesfernandez2023desinformation"].authors
        == ["Manuel Robles Fernandez"]
    )


def test_latex_parser_deduplicates_bibliography_resource_paths(
    tmp_path: Path,
) -> None:
    parser = LatexParser()
    source = tmp_path / "CR.tex"
    bibliography_dir = tmp_path / "bibliographies"
    bibliography_dir.mkdir()
    resource_path = bibliography_dir / "articles.bib"
    resource_path.write_text("", encoding="utf-8")
    content = (
        "\\addbibresource{bibliographies/articles.bib}\n"
        "\\addbibresource{bibliographies/articles.bib}\n"
    )

    bibliography_paths = parser._extract_bibliography_paths(content, source)

    assert bibliography_paths == [str(resource_path.resolve())]


def test_latex_parser_skips_citation_links_without_clean_text() -> None:
    parser = LatexParser()

    citation_links = parser._extract_citation_links(
        current_content="\\footcite{dupont2024}",
        cleaned_content="",
    )

    assert citation_links == []


def test_latex_parser_parses_bibliographic_entry_fields() -> None:
    parser = LatexParser()

    key, reference = parser._parse_bibliographic_entry(
        "@online{dupont2024,\n"
        "  author = {Jean Dupont and Marie Martin},\n"
        '  title = "Titre Exemple",\n'
        "  year = {2024},\n"
        "  url = {https://example.org}\n"
        "}",
        Path("tests/parsing/fixtures/bibliographies/online.bib"),
    )

    assert key == "dupont2024"
    assert reference.entry_type == "online"
    assert reference.title == "Titre Exemple"
    assert reference.authors == ["Jean Dupont", "Marie Martin"]
    assert reference.year == "2024"
    assert reference.raw_entry["url"] == "https://example.org"


def test_latex_parser_skips_missing_bibliography_paths(tmp_path: Path) -> None:
    parser = LatexParser()

    references = parser._load_bibliography_entries(
        [str(tmp_path / "missing.bib")]
    )

    assert references == {}


def test_latex_parser_returns_empty_entries_for_bib_file_without_entries(
    tmp_path: Path,
) -> None:
    parser = LatexParser()
    bib_file = tmp_path / "empty.bib"
    bib_file.write_text("This file has no bib entries.", encoding="utf-8")

    references = parser._parse_bib_file(bib_file)

    assert references == {}


def test_latex_parser_returns_empty_entries_for_bib_file_without_opening_brace(
    tmp_path: Path,
) -> None:
    parser = LatexParser()
    bib_file = tmp_path / "invalid_header.bib"
    bib_file.write_text("@article", encoding="utf-8")

    references = parser._parse_bib_file(bib_file)

    assert references == {}


def test_latex_parser_raises_for_invalid_bibliographic_entry() -> None:
    parser = LatexParser()
    path = Path("tests/parsing/fixtures/bibliographies/online.bib")

    with pytest.raises(ValueError, match="Invalid bibliographic entry"):
        parser._parse_bibliographic_entry("@online invalid", path)


def test_latex_parser_ignores_bib_chunks_without_assignment() -> None:
    parser = LatexParser()

    fields = parser._parse_bib_fields(
        "title = {Titre Exemple}, invalid chunk, year = {2024}"
    )

    assert fields == {"title": "Titre Exemple", "year": "2024"}


def test_latex_parser_falls_back_to_global_find_when_search_start_misses(
    monkeypatch,
) -> None:
    parser = LatexParser()

    monkeypatch.setattr(
        parser,
        "_extract_citation_segments",
        lambda _: [
            "Phrase dupliquee\\footcite{dupont2024}.",
            "Phrase dupliquee\\footcite{dupont2024}.",
        ],
    )

    citation_links = parser._extract_citation_links(
        current_content="ignored",
        cleaned_content="Phrase dupliquee.",
    )

    assert citation_links == [
        {
            "start": 0,
            "end": len("Phrase dupliquee."),
            "text": "Phrase dupliquee.",
            "citations": ["dupont2024"],
        },
        {
            "start": 0,
            "end": len("Phrase dupliquee."),
            "text": "Phrase dupliquee.",
            "citations": ["dupont2024"],
        },
    ]


def test_latex_parser_skips_citation_link_when_text_cannot_be_found(
    monkeypatch,
) -> None:
    parser = LatexParser()

    monkeypatch.setattr(
        parser,
        "_extract_citation_segments",
        lambda _: ["Phrase absente\\footcite{dupont2024}."],
    )

    citation_links = parser._extract_citation_links(
        current_content="ignored",
        cleaned_content="Un autre contenu.",
    )

    assert citation_links == []


def test_latex_parser_extracts_one_citation_link_per_itemize_item(
    tmp_path: Path,
) -> None:
    source = tmp_path / "CR_itemize_citations.tex"
    source.write_text(
        "\\section{Liste}\n"
        "Introduction sans citation.\n"
        "\\begin{itemize}\n"
        "\\item Premier point\\footcite{dupont2024}\n"
        "\\item Deuxieme point\\footcite{martin2023, dupont2024}\n"
        "\\end{itemize}\n",
        encoding="utf-8",
    )

    document = LatexParser().parse(source)

    section = document.root_nodes[0]
    assert section.metadata["citations"] == ["dupont2024", "martin2023"]
    assert set(document.bibliography) == {"dupont2024", "martin2023"}
    assert section.metadata["citation_links"] == [
        {
            "start": section.content.find("Premier point"),
            "end": section.content.find("Premier point") + len("Premier point"),
            "text": "Premier point",
            "citations": ["dupont2024"],
        },
        {
            "start": section.content.find("Deuxieme point"),
            "end": section.content.find("Deuxieme point") + len("Deuxieme point"),
            "text": "Deuxieme point",
            "citations": ["martin2023", "dupont2024"],
        },
    ]
