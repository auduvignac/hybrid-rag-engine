"""Document domain models used by the parsing layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hybrid_rag.domain.enums import NodeType


@dataclass(slots=True)
class DocumentNode:
    """Structured node extracted from a source document."""

    title: str
    level: int
    content: str = ""
    node_type: str = NodeType.PART
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list["DocumentNode"] = field(default_factory=list)

    def add_child(self, child: "DocumentNode") -> None:
        """Append a child node to the current node."""

        self.children.append(child)


@dataclass(slots=True)
class BibliographicReference:
    """Normalized bibliographic entry keyed by citation id."""

    title: str | None = None
    authors: list[str] = field(default_factory=list)
    year: str | None = None
    entry_type: str | None = None
    raw_entry: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    """Normalized parsing output shared across input formats."""

    source_path: str
    document_type: str
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    bibliography: dict[str, BibliographicReference] = field(default_factory=dict)
    root_nodes: list[DocumentNode] = field(default_factory=list)

    def add_root_node(self, node: DocumentNode) -> None:
        """Append a top-level node to the parsed document."""

        self.root_nodes.append(node)

    def add_bibliographic_reference(
        self, key: str, reference: BibliographicReference
    ) -> None:
        """Register a bibliographic reference once for the full document."""

        existing = self.bibliography.get(key)
        if existing is None:
            self.bibliography[key] = reference
            return

        if reference.title:
            existing.title = reference.title
        if reference.authors:
            existing.authors = reference.authors
        if reference.year:
            existing.year = reference.year
        if reference.entry_type:
            existing.entry_type = reference.entry_type
        if reference.raw_entry:
            existing.raw_entry = reference.raw_entry
