# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoRAG is a RAG AutoML tool that automatically finds optimal RAG (Retrieval-Augmented Generation) pipelines for your data. It evaluates various RAG module combinations and selects the best configuration for your use case.

## Build & Development Commands

### Installation
```bash
# Create virtual environment with uv (recommended)
uv venv && source .venv/bin/activate
uv sync --all-extras

# Or with pip
pip install -e '.[all]'

# Required post-install steps
pip install --upgrade pyOpenSSL nltk
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"
```

### Linting & Formatting
```bash
ruff check --fix
ruff format
```

Pre-commit hooks are configured - run `pre-commit install` after cloning.

### Testing
```bash
# Run all tests
python -m pytest -o log_cli=true --log-cli-level=INFO -n auto tests

# Run specific test file
python -m pytest tests/autorag/path/to/test_file.py

# Many tests require OPENAI_API_KEY in pytest.ini or environment
```

### CLI Commands
```bash
autorag evaluate --config config.yaml --qa_data_path qa.parquet --corpus_data_path corpus.parquet
autorag validate --config config.yaml --qa_data_path qa.parquet --corpus_data_path corpus.parquet
autorag run_api --trial_dir ./trial --host 0.0.0.0 --port 8000
autorag dashboard --trial_dir ./trial --port 7690
autorag run_web --trial_path ./trial
```

## Architecture

### Core Concepts

AutoRAG uses a **node-line architecture** where RAG pipelines are defined as sequences of nodes:

1. **Node Lines**: Groups of nodes that process data sequentially (defined in YAML config under `node_lines`)
2. **Nodes**: Processing stages in the pipeline (e.g., `lexical_retrieval`, `semantic_retrieval`, `prompt_maker`, `generator`)
3. **Modules**: Specific implementations within each node (e.g., `bm25` module in `lexical_retrieval` node)

### Evaluation Flow

```
Evaluator (autorag/evaluator.py)
    └── Loads YAML config with node_lines
    └── Ingests corpus to BM25/VectorDB
    └── run_node_line (autorag/node_line.py)
        └── For each Node in node_line:
            └── Node.run() evaluates all modules
            └── Selects best module based on metrics
    └── Outputs summary.csv with best pipeline
```

### Key Node Types (autorag/nodes/)

| Node Type | Purpose |
|-----------|---------|
| `lexicalretrieval` | BM25-based retrieval |
| `semanticretrieval` | Vector DB retrieval (vectordb module) |
| `hybridretrieval` | Combines lexical + semantic (hybrid_rrf, hybrid_cc) |
| `passagereranker` | Reranks retrieved passages |
| `passagefilter` | Filters passages by threshold/percentile |
| `passageaugmenter` | Augments passages with context |
| `passagecompressor` | Compresses/summarizes passages |
| `queryexpansion` | Expands queries (hyde, multi_query) |
| `promptmaker` | Creates prompts from query + passages |
| `generator` | LLM generation (openai_llm, llama_index_llm, vllm) |

### Data Pipeline (autorag/data/)

- **parse/**: Document parsing (langchain_parse, llamaparse, clova)
- **chunk/**: Text chunking (langchain_chunk, llama_index_chunk)
- **qa/**: QA dataset creation (query generation, answer generation, filtering)

### Data Formats

- **QA Dataset** (qa.parquet): Contains queries, ground truth answers, and retrieval_gt (ground truth document IDs)
- **Corpus Dataset** (corpus.parquet): Contains doc_id, contents, and metadata

### YAML Config Structure

```yaml
vectordb:            # Vector DB configurations
node_lines:
  - node_line_name: retrieve_node_line
    nodes:
      - node_type: lexical_retrieval
        strategy:
          metrics: [retrieval_f1, retrieval_recall]
        modules:
          - module_type: bm25
      - node_type: semantic_retrieval
        # ...
  - node_line_name: post_retrieve_node_line
    nodes:
      - node_type: prompt_maker
        # ...
      - node_type: generator
        # ...
```

## Key File Locations

- **CLI entry point**: [cli.py](autorag/cli.py)
- **Evaluator**: [evaluator.py](autorag/evaluator.py)
- **Node runner**: [node_line.py](autorag/node_line.py)
- **Schema definitions**: [schema/](autorag/schema/)
- **Sample configs**: [sample_config/](sample_config/) (rag/, chunk/, parse/)
- **Vector DB integrations**: [vectordb/](autorag/vectordb/)
- **Deployment**: [deploy/](autorag/deploy/) (api.py, gradio.py)

## Testing Notes

- Tests requiring CUDA should use `@pytest.mark.skipif(is_github_action())`
- Tests using external APIs must use mocks and pytest fixtures
- Tests should not leave extra files behind
