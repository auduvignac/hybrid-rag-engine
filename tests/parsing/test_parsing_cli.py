import json
from pathlib import Path

import hybrid_rag.parsing.cli as cli_module
from hybrid_rag.parsing.cli import _document_to_dict, main
from hybrid_rag.domain import (
    BibliographicReference,
    DocumentNode,
    NodeType,
    ParsedDocument,
)


def test_document_to_dict_json_serializable() -> None:
    child = DocumentNode(
        title="Child",
        level=2,
        node_type=NodeType.SUBSECTION,
        content="Child content",
    )
    parent = DocumentNode(
        title="Parent",
        level=1,
        node_type=NodeType.SECTION,
        content="Parent content",
    )
    parent.add_child(child)

    parsed = ParsedDocument(
        source_path="source.tex",
        document_type="latex",
        title="Parent",
    )
    parsed.add_root_node(parent)
    parsed.add_bibliographic_reference(
        "RefKey",
        BibliographicReference(
            title="A Reference Title",
            authors=["Author Name"],
            year="2024",
            entry_type="article",
            raw_entry={"url": "https://example.org"},
        ),
    )

    as_dict = _document_to_dict(parsed)

    assert as_dict["source_path"] == "source.tex"
    assert as_dict["document_type"] == "latex"
    assert as_dict["title"] == "Parent"
    assert len(as_dict["root_nodes"]) == 1
    assert list(as_dict["bibliography"]) == ["RefKey"]

    root_node = as_dict["root_nodes"][0]
    assert root_node["title"] == "Parent"
    assert root_node["level"] == 1
    assert root_node["node_type"] == NodeType.SECTION.value
    assert root_node["content"] == "Parent content"
    assert len(root_node["children"]) == 1

    child_node = root_node["children"][0]
    assert child_node["title"] == "Child"
    assert child_node["level"] == 2
    assert child_node["node_type"] == NodeType.SUBSECTION.value
    assert child_node["content"] == "Child content"

    bib_dict = as_dict["bibliography"]["RefKey"]
    assert bib_dict["title"] == "A Reference Title"
    assert bib_dict["authors"] == ["Author Name"]
    assert bib_dict["year"] == "2024"
    assert bib_dict["entry_type"] == "article"
    assert bib_dict["raw_entry"]["url"] == "https://example.org"

    json.dumps(as_dict)


def _write_temp_source(tmp_path: Path) -> Path:
    source = tmp_path / "doc.tex"
    source.write_text(
        (
            "\\section{Intro}\n"
            "Some content \\cite{dupont2024}.\n\n"
            "\\subsection{Background}\n"
            "More content.\n"
        ),
        encoding="utf-8",
    )
    return source


def _write_temp_source_with_bibliography(tmp_path: Path) -> Path:
    bibliography_dir = tmp_path / "bibliographies"
    bibliography_dir.mkdir()
    bib_file = bibliography_dir / "refs.bib"
    bib_file.write_text(
        (
            "@online{dupont2024,\n"
            "  title = {Reference Title},\n"
            "  year = {2024}\n"
            "}\n"
        ),
        encoding="utf-8",
    )

    source = tmp_path / "doc_with_bib.tex"
    source.write_text(
        (
            "\\addbibresource{bibliographies/refs.bib}\n"
            "\\section{Intro}\n"
            "Some content\\parentcite{dupont2024}.\n"
        ),
        encoding="utf-8",
    )
    return source


def test_cli_main_json_output_success(tmp_path: Path, capsys) -> None:
    source_path = _write_temp_source(tmp_path)

    exit_code = main(["--json", str(source_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    parsed_output = json.loads(captured.out)
    assert parsed_output["source_path"].endswith("doc.tex")
    assert parsed_output["document_type"] == "latex"
    assert isinstance(parsed_output["root_nodes"], list)


def test_cli_main_summary_output_success(tmp_path: Path, capsys) -> None:
    source_path = _write_temp_source(tmp_path)

    exit_code = main([str(source_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out
    assert "doc.tex" in captured.out or "Intro" in captured.out
    assert "citations: dupont2024" in captured.out
    assert "Bibliography entries: 1" in captured.out


def test_cli_main_summary_output_with_resolved_bibliography(
    tmp_path: Path, capsys
) -> None:
    source_path = _write_temp_source_with_bibliography(tmp_path)

    exit_code = main([str(source_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "citations: dupont2024" in captured.out
    assert "Bibliography entries: 1" in captured.out


def test_cli_main_nonexistent_file_error(capsys) -> None:
    exit_code = main(["--json", "missing.tex"])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert captured.err
    assert "Traceback" not in captured.err


def test_cli_main_debug_mode_shows_traceback(capsys) -> None:
    exit_code = main(["--json", "--debug", "missing.tex"])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "Traceback" in captured.err


def test_cli_main_keyboard_interrupt_returns_130(monkeypatch, capsys) -> None:
    def raise_interrupt(_source):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module, "parse_document", raise_interrupt)

    exit_code = main(["missing.tex"])
    captured = capsys.readouterr()

    assert exit_code == 130
    assert "Parsing cancelled by user." in captured.err
