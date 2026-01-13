# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoRAG is a RAG (Retrieval-Augmented Generation) AutoML tool that automatically finds optimal RAG pipelines for your data. It evaluates various RAG module combinations to identify the best configuration for specific use cases.

## Development Commands

### git commit 하기전

수정사항을 CHANGELOG.md에 추가하자.

### Installation
```bash
# Using UV (recommended)
uv venv && source .venv/bin/activate
uv pip install -r pyproject.toml --all-extras -e . --timeout 3600

# Using pip
pip install -e '.[all]' --timeout 3600
```

### Code Quality
```bash
ruff check --fix
ruff format
pre-commit run --all-files
```

### Testing
```bash
# Clean conflicting test packages first
python tests/delete_tests.py

# Run full test suite
python -m pytest -o log_cli=true --log-cli-level=INFO -n auto tests/autorag --timeout 1800

# Run specific test file
python -m pytest tests/autorag/path/to/test_file.py
```

Note: Many tests require `OPENAI_API_KEY` environment variable. Create `pytest.ini`:
```ini
[pytest]
env =
    OPENAI_API_KEY=sk-xxxx
log_cli=true
log_cli_level=INFO
```

### CLI Usage
```bash
autorag --help
autorag evaluate --config config.yaml --qa_data_path qa.parquet --corpus_data_path corpus.parquet
autorag validate --config config.yaml --qa_data_path qa.parquet --corpus_data_path corpus.parquet
autorag dashboard --trial_dir ./trial_dir --port 7690
autorag run_api --trial_path ./trial --host 0.0.0.0 --port 8000
```

## Architecture

### Core Pipeline Flow

AutoRAG uses a node-based pipeline architecture where data flows through discrete RAG stages:

1. **Evaluator** (`autorag/evaluator.py`): Orchestrates pipeline evaluation, manages trials, handles QA/corpus data loading
2. **Node Lines**: Sequential execution of nodes defined in YAML config
3. **Nodes** (`autorag/nodes/`): Discrete RAG stages (retrieval, reranking, generation, etc.)
4. **Strategy** (`autorag/strategy.py`): Selection algorithms to choose best performing modules

### Key Directories

```
autorag/
├── cli.py              # Command-line interface entry point
├── evaluator.py        # Main evaluation orchestrator
├── nodes/              # RAG pipeline nodes
│   ├── lexicalretrieval/   # BM25-based retrieval
│   ├── semanticretrieval/  # Vector DB retrieval
│   ├── hybridretrieval/    # Hybrid approaches (RRF, CC)
│   ├── passagereranker/    # 15+ reranker implementations
│   ├── queryexpansion/     # HyDE, MultiQuery, QueryDecompose
│   ├── generator/          # LLM answer generation
│   └── promptmaker/        # Prompt template generation
├── vectordb/           # Vector DB integrations (Milvus, Chroma, Weaviate, Pinecone, Qdrant, Couchbase)
├── data/
│   ├── parse/          # Document parsing (Langchain, LlamaParse, Clova OCR)
│   ├── chunk/          # Document chunking (token, semantic, overlap)
│   └── qa/             # QA dataset creation and manipulation
├── deploy/             # API server and web interface
└── evaluation/         # Metric implementations
```

### Configuration-Driven Design

Pipelines are defined via YAML configs (see `sample_config/`). The system:
- Dynamically loads modules via `support.py` registry
- Tests parameter combinations exhaustively
- Stores results as DataFrames with summary CSVs

### Data Flow

- Data flows as pandas DataFrames through the pipeline
- Each node adds/modifies columns
- Parquet files used for corpus and QA datasets
- Trial results stored in structured folder hierarchy

## Testing Patterns

- Use mocks for heavy GPU models and external API calls
- Tests requiring CUDA: mark with `@pytest.mark.skipif(is_github_action())`
- Tests must not leave extra files behind
- See `tests/mock.py` for mock implementations
