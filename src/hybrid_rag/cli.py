"""Command-line interface for the hybrid RAG parser."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from hybrid_rag.domain.documents import (
    BibliographicReference,
    DocumentNode,
    ParsedDocument,
)
from hybrid_rag.parsing.service import parse_document


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the hybrid-rag document parsing pipeline on a source file."
    )
    parser.add_argument(
        "source", type=Path, help="Path to the source document to parse."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the parsed document as formatted JSON.",
    )
    parser.add_argument(
        "-v",
        "--debug",
        action="store_true",
        help="Enable verbose debug output with full tracebacks on errors.",
    )
    return parser


def _node_to_dict(node: DocumentNode) -> dict[str, Any]:
    return {
        "title": node.title,
        "level": node.level,
        "content": node.content,
        "node_type": node.node_type.value,
        "metadata": node.metadata,
        "children": [_node_to_dict(child) for child in node.children],
    }


def _reference_to_dict(reference: BibliographicReference) -> dict[str, Any]:
    return {
        "title": reference.title,
        "authors": reference.authors,
        "year": reference.year,
        "entry_type": reference.entry_type,
        "raw_entry": reference.raw_entry,
    }


def _document_to_dict(document: ParsedDocument) -> dict[str, Any]:
    return {
        "source_path": document.source_path,
        "document_type": document.document_type,
        "title": document.title,
        "metadata": document.metadata,
        "bibliography": {
            key: _reference_to_dict(reference)
            for key, reference in document.bibliography.items()
        },
        "root_nodes": [_node_to_dict(node) for node in document.root_nodes],
    }


def _print_summary(document: ParsedDocument) -> None:
    print(f"Source: {document.source_path}")
    print(f"Type: {document.document_type}")
    print(f"Title: {document.title or '<none>'}")
    print(f"Root nodes: {len(document.root_nodes)}")
    print(f"Bibliography entries: {len(document.bibliography)}")
    for node in document.root_nodes:
        _print_node(node)


def _print_node(node: DocumentNode, indent: int = 0) -> None:
    prefix = "  " * indent
    print(f"{prefix}- [{node.node_type.value}] {node.title}")
    if citations := node.metadata.get("citations", []):
        print(f"{prefix}  citations: {', '.join(citations)}")
    if node.content:
        preview = node.content[:200].replace("\n", " ")
        suffix = "..." if len(node.content) > 200 else ""
        print(f"{prefix}  content: {preview}{suffix}")
    for child in node.children:
        _print_node(child, indent + 1)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        document = parse_document(args.source)
    except Exception as error:
        print(f"Parsing failed: {error}", file=sys.stderr)
        if args.debug:
            print("\nFull traceback (debug mode enabled):", file=sys.stderr)
            traceback.print_exc()
        return 1

    if args.json:
        print(json.dumps(_document_to_dict(document), indent=2, ensure_ascii=False))
    else:
        _print_summary(document)

    return 0
