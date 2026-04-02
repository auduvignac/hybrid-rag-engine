"""Chunking strategy based on structured document nodes."""

from __future__ import annotations

import hashlib
import json

from hybrid_rag.chunking.base import BaseChunker
from hybrid_rag.domain.chunks import Chunk
from hybrid_rag.domain.documents import DocumentNode, ParsedDocument


class DocumentNodeChunker(BaseChunker):
    """Create one chunk per non-empty document node content."""

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        self._visit_node(document=document, chunks=chunks)
        return chunks

    def _visit_node(
        self,
        document: ParsedDocument,
        chunks: list[Chunk],
    ) -> None:
        stack: list[tuple[DocumentNode, list[str], list[int]]] = [
            (root_node, [], [root_index])
            for root_index, root_node in reversed(list(enumerate(document.root_nodes)))
        ]

        while stack:
            node, section_path, ordinal_path = stack.pop()
            current_path = [*section_path, node.title]
            if node.content.strip():
                metadata = dict(node.metadata)
                metadata["content_hash"] = self._build_content_hash(node.content)
                chunks.append(
                    Chunk(
                        chunk_id=self._build_chunk_id(
                            document=document,
                            node=node,
                            section_path=current_path,
                            ordinal_path=ordinal_path,
                        ),
                        source_path=document.source_path,
                        document_type=document.document_type,
                        text=node.content,
                        title=node.title,
                        section_path=current_path,
                        node_type=node.node_type,
                        metadata=metadata,
                    )
                )

            stack.extend(
                (child, current_path, [*ordinal_path, child_index])
                for child_index, child in reversed(list(enumerate(node.children)))
            )

    def _build_chunk_id(
        self,
        document: ParsedDocument,
        node: DocumentNode,
        section_path: list[str],
        ordinal_path: list[int],
    ) -> str:
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

    def _build_content_hash(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()
