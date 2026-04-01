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
class ParsedDocument:
    """Normalized parsing output shared across input formats."""

    source_path: str
    document_type: str
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    root_nodes: list[DocumentNode] = field(default_factory=list)

    def add_root_node(self, node: DocumentNode) -> None:
        """Append a top-level node to the parsed document."""

        self.root_nodes.append(node)
