# hybrid-rag-engine

Hybrid-RAG-Engine is a provenance-aware hybrid retrieval-augmented generation pipeline that combines semantic and lexical search to deliver accurate, grounded, and traceable question answering over structured document collections.

## Development Setup

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

## Run Tests

Run the full test suite with coverage:

```bash
python -m pytest -s --log-cli-level=INFO --cov=src/hybrid_rag --cov-report=term-missing --cov-report=html
```

Run a single test with coverage:

```bash
python -m pytest -s --log-cli-level=INFO --cov=src/hybrid_rag --cov-report=term-missing --cov-report=html tests/parsing/test_latex_parser.py::test_latex_parser_builds_expected_hierarchy
```

## Reading References

- [Building LLM Powered Applications](docs/reading/building-llm-powered-applications.md)
