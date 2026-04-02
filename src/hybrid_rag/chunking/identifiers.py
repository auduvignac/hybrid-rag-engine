"""Shared helpers for chunk identifiers and content hashes."""

from __future__ import annotations

import hashlib
import json

from hybrid_rag.domain.documents import DocumentNode, ParsedDocument


def build_chunk_id(
    document: ParsedDocument,
    node: DocumentNode,
    section_path: list[str],
    ordinal_path: list[int],
) -> str:
    """Build a deterministic structural identifier for a chunk."""

    payload = {
        "source_path": document.source_path,
        "document_type": document.document_type,
        "section_path": section_path,
        "node_type": node.node_type.value,
        "ordinal_path": ordinal_path,
    }
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build_content_hash(text: str) -> str:
    """Build a deterministic hash for chunk textual content."""

    return hashlib.sha1(text.encode("utf-8")).hexdigest()
