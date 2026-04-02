from hybrid_rag.chunking import (
    DocumentNodeChunker,
    build_chunk_id,
    build_content_hash,
    chunk_document,
)
from hybrid_rag.domain import Chunk, DocumentNode, NodeType, ParsedDocument


def test_document_node_chunker_builds_chunks_from_non_empty_nodes() -> None:
    subsection = DocumentNode(
        title="Background",
        level=2,
        content="Background content",
        node_type=NodeType.SUBSECTION,
        metadata={"citations": ["dupont2024"]},
    )
    section = DocumentNode(
        title="Intro",
        level=1,
        content="Intro content",
        node_type=NodeType.SECTION,
        metadata={"sectioning_level": 2},
        children=[subsection],
    )
    empty_section = DocumentNode(
        title="Empty",
        level=1,
        content="",
        node_type=NodeType.SECTION,
    )
    document = ParsedDocument(
        source_path="docs/CR_001.tex",
        document_type="latex",
        title="Report",
        root_nodes=[section, empty_section],
    )

    chunks = DocumentNodeChunker().chunk(document)

    assert len(chunks) == 2
    assert all(isinstance(chunk, Chunk) for chunk in chunks)

    first_chunk = chunks[0]
    assert first_chunk.chunk_id == build_chunk_id(
        document=document,
        node=section,
        section_path=["Intro"],
        ordinal_path=[0],
    )
    assert first_chunk.text == "Intro content"
    assert first_chunk.title == "Intro"
    assert first_chunk.section_path == ["Intro"]
    assert first_chunk.node_type == NodeType.SECTION
    assert first_chunk.metadata == {
        "sectioning_level": 2,
        "content_hash": build_content_hash("Intro content"),
    }

    second_chunk = chunks[1]
    assert second_chunk.chunk_id == build_chunk_id(
        document=document,
        node=subsection,
        section_path=["Intro", "Background"],
        ordinal_path=[0, 0],
    )
    assert second_chunk.text == "Background content"
    assert second_chunk.section_path == ["Intro", "Background"]
    assert second_chunk.node_type == NodeType.SUBSECTION
    assert second_chunk.metadata == {
        "citations": ["dupont2024"],
        "content_hash": build_content_hash("Background content"),
    }


def test_chunk_document_uses_default_strategy() -> None:
    document = ParsedDocument(
        source_path="docs/CR_002.tex",
        document_type="latex",
        root_nodes=[
            DocumentNode(
                title="Only Section",
                level=1,
                content="Some text",
                node_type=NodeType.SECTION,
            )
        ],
    )

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].section_path == ["Only Section"]
    assert chunks[0].metadata["content_hash"] == build_content_hash("Some text")


def test_document_node_chunker_preserves_depth_first_order_iteratively() -> None:
    first_child = DocumentNode(
        title="First Child",
        level=2,
        content="First child content",
        node_type=NodeType.SUBSECTION,
    )
    second_child = DocumentNode(
        title="Second Child",
        level=2,
        content="Second child content",
        node_type=NodeType.SUBSECTION,
    )
    first_root = DocumentNode(
        title="First Root",
        level=1,
        content="First root content",
        node_type=NodeType.SECTION,
        children=[first_child, second_child],
    )
    second_root = DocumentNode(
        title="Second Root",
        level=1,
        content="Second root content",
        node_type=NodeType.SECTION,
    )
    document = ParsedDocument(
        source_path="docs/CR_003.tex",
        document_type="latex",
        root_nodes=[first_root, second_root],
    )

    chunks = DocumentNodeChunker().chunk(document)

    assert [chunk.title for chunk in chunks] == [
        "First Root",
        "First Child",
        "Second Child",
        "Second Root",
    ]
    assert len({chunk.chunk_id for chunk in chunks}) == 4
    assert all(len(chunk.chunk_id) == 40 for chunk in chunks)


def test_chunk_document_instantiates_default_chunker_per_call(monkeypatch) -> None:
    instances: list[TrackingChunker] = []

    class TrackingChunker(DocumentNodeChunker):
        def __init__(self) -> None:
            super().__init__()
            instances.append(self)

    document = ParsedDocument(
        source_path="docs/CR_004.tex",
        document_type="latex",
        root_nodes=[
            DocumentNode(
                title="Only Section",
                level=1,
                content="Some text",
                node_type=NodeType.SECTION,
            )
        ],
    )

    monkeypatch.setattr(
        "hybrid_rag.chunking.service.DocumentNodeChunker",
        TrackingChunker,
    )

    first_chunks = chunk_document(document)
    second_chunks = chunk_document(document)

    assert len(first_chunks) == 1
    assert len(second_chunks) == 1
    assert len(instances) == 2
    assert instances[0] is not instances[1]
