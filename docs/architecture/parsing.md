# Parsing Architecture

The parsing layer converts source documents into a normalized, provenance-friendly
object model before any chunking or retrieval concerns are introduced.

## Why It Exists

Parsing is responsible for structural extraction only:

- load a source file
- normalize its textual representation
- extract a document tree and lightweight metadata

Chunking is intentionally separate because chunk boundaries, token budgets and
retrieval strategies are downstream concerns that should operate on a stable
parsed representation instead of being hard-coded into format-specific parsers.

## Patterns Used

- Strategy: one parser implementation per source type, such as `LatexParser`
  or a future `PdfParser`
- Template Method: `BaseParser.parse()` orchestrates the common pipeline
- Factory Method / Registry: `ParserFactory` asks `ParserRegistry` for the
  appropriate parser based on the source path
- Composite: `ParsedDocument` contains `DocumentNode` trees

## Main Classes

- `DocumentNode`: a structured node with title, level, text content, metadata
  and children
- `ParsedDocument`: normalized parsing result for one source document
- `BaseParser`: abstract parsing contract and shared pipeline
- `ParserRegistry`: parser class registration by extension
- `ParserFactory`: parser instantiation entry point
- `ParsingService`: façade used by the rest of the pipeline

## Example Output

```python
ParsedDocument(
    source_path="docs/CR_001.tex",
    document_type="latex",
    title="Compte Rendu Projet",
    metadata={},
    root_nodes=[
        DocumentNode(
            title="Introduction",
            level=1,
            content="Ce document présente un prototype de parsing.",
            node_type="section",
            metadata={},
            children=[],
        )
    ],
)
```

This normalized shape is designed to remain stable across input formats so that
future PDF or other parsers can feed the same downstream pipeline.
