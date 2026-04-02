"""Command-line interface for the hybrid RAG chunking pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from hybrid_rag.chunking.service import chunk_document
from hybrid_rag.cli_common import add_debug_argument, run_cli_action
from hybrid_rag.domain.chunks import Chunk
from hybrid_rag.parsing.service import parse_document


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse a source file and display the resulting retrieval chunks."
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to the source document to parse and chunk.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the generated chunks as formatted JSON.",
    )
    add_debug_argument(parser)
    return parser


def _chunk_to_dict(chunk: Chunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "source_path": chunk.source_path,
        "document_type": chunk.document_type,
        "title": chunk.title,
        "section_path": chunk.section_path,
        "node_type": (
            chunk.node_type.value if chunk.node_type is not None else None
        ),
        "text": chunk.text,
        "metadata": chunk.metadata,
    }


def _print_summary(chunks: list[Chunk]) -> None:
    if not chunks:
        print("Chunks: 0")
        return

    print(f"Source: {chunks[0].source_path}")
    print(f"Type: {chunks[0].document_type}")
    print(f"Chunks: {len(chunks)}")
    for chunk in chunks:
        _print_chunk(chunk)


def _print_chunk(chunk: Chunk) -> None:
    print(f"- {chunk.chunk_id}")
    print(
        f"  node_type: {chunk.node_type.value if chunk.node_type else '<none>'}"
    )
    print(f"  title: {chunk.title or '<none>'}")
    print(f"  section_path: {' > '.join(chunk.section_path) or '<none>'}")
    if citations := chunk.metadata.get("citations", []):
        print(f"  citations: {', '.join(citations)}")
    preview = chunk.text[:200].replace("\n", " ")
    suffix = "..." if len(chunk.text) > 200 else ""
    print(f"  text: {preview}{suffix}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    def _chunk_action() -> list[Chunk]:
        document = parse_document(args.source)
        return chunk_document(document)

    exit_code, chunks = run_cli_action(
        _chunk_action,
        operation_name="Chunking",
        debug=args.debug,
        cancel_message="Chunking cancelled by user.",
    )
    if exit_code != 0 or chunks is None:
        return exit_code

    if args.json:
        print(
            json.dumps(
                [_chunk_to_dict(chunk) for chunk in chunks],
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
    else:
        _print_summary(chunks)

    return 0
