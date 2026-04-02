import json
from pathlib import Path

import hybrid_rag.chunking.cli as chunking_cli_module
from hybrid_rag.chunking.cli import _chunk_to_dict, main
from hybrid_rag.domain import Chunk, NodeType


def test_chunk_to_dict_json_serializable() -> None:
    chunk = Chunk(
        chunk_id="doc.tex::node.0",
        source_path="doc.tex",
        document_type="latex",
        text="Intro content",
        title="Intro",
        section_path=["Intro"],
        node_type=NodeType.SECTION,
        metadata={"citations": ["dupont2024"]},
    )

    as_dict = _chunk_to_dict(chunk)

    assert as_dict["chunk_id"] == "doc.tex::node.0"
    assert as_dict["source_path"] == "doc.tex"
    assert as_dict["document_type"] == "latex"
    assert as_dict["title"] == "Intro"
    assert as_dict["section_path"] == ["Intro"]
    assert as_dict["node_type"] == "section"
    assert as_dict["text"] == "Intro content"
    assert as_dict["metadata"] == {"citations": ["dupont2024"]}

    json.dumps(as_dict)


def _write_temp_source(tmp_path: Path) -> Path:
    source = tmp_path / "doc.tex"
    source.write_text(
        (
            "\\section{Intro}\n"
            "Some content \\footcite{dupont2024}.\n\n"
            "\\subsection{Background}\n"
            "More content.\n"
        ),
        encoding="utf-8",
    )
    return source


def test_chunking_cli_main_json_output_success(
    tmp_path: Path, capsys
) -> None:
    source_path = _write_temp_source(tmp_path)

    exit_code = main(["--json", str(source_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert len(payload) == 2
    assert len(payload[0]["chunk_id"]) == 40
    assert payload[0]["node_type"] == "section"
    assert payload[0]["section_path"] == ["Intro"]
    assert payload[0]["metadata"]["citations"] == ["dupont2024"]
    assert "content_hash" in payload[0]["metadata"]


def test_chunking_cli_main_summary_output_success(
    tmp_path: Path, capsys
) -> None:
    source_path = _write_temp_source(tmp_path)

    exit_code = main([str(source_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Chunks: 2" in captured.out
    assert "section_path: Intro" in captured.out
    assert "section_path: Intro > Background" in captured.out
    assert "citations: dupont2024" in captured.out


def test_chunking_cli_main_nonexistent_file_error(capsys) -> None:
    exit_code = main(["missing.tex"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Chunking failed:" in captured.err
    assert "Traceback" not in captured.err


def test_chunking_cli_main_debug_mode_shows_traceback(capsys) -> None:
    exit_code = main(["--debug", "missing.tex"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Traceback" in captured.err


def test_chunking_cli_main_keyboard_interrupt_returns_130(
    monkeypatch, capsys
) -> None:
    def raise_interrupt(_source):
        raise KeyboardInterrupt

    monkeypatch.setattr(chunking_cli_module, "parse_document", raise_interrupt)

    exit_code = main(["missing.tex"])
    captured = capsys.readouterr()

    assert exit_code == 130
    assert "Chunking cancelled by user." in captured.err
