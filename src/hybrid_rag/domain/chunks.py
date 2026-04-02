"""Chunk domain models derived from parsed documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hybrid_rag.domain.enums import NodeType


@dataclass(slots=True)
class Chunk:
    """Normalized chunk ready for retrieval-oriented downstream processing."""

    chunk_id: str
    source_path: str
    document_type: str
    text: str
    title: str | None = None
    section_path: list[str] = field(default_factory=list)
    node_type: NodeType | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
