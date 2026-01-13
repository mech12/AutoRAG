.PHONY: help install install-dev setup-nltk lint format check test test-clean \
        quick-test quick-test-custom evaluate dashboard api web validate clean

# Default target
.DEFAULT_GOAL := help

# Variables
VENV := .venv
PYTHON := python
PROJECT_DIR := logs
TRIAL_DIR := logs/0
CONFIG := sample_config/rag/korean/non_gpu/simple_korean.yaml
CONFIG_CUSTOM := sample_config/rag/korean/non_gpu/simple_korean_custom.yaml
SAMPLE_QA := tests/resources/dataset_sample_gen_by_autorag/qa.parquet
SAMPLE_CORPUS := tests/resources/dataset_sample_gen_by_autorag/corpus.parquet
QA_DATA := qa.parquet
CORPUS_DATA := corpus.parquet
API_HOST := 0.0.0.0
API_PORT := 8000
DASHBOARD_PORT := 7690

##@ General
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Installation
install: ## Install AutoRAG (basic)
	pip install AutoRAG

install-gpu: ## Install AutoRAG with GPU support
	pip install "AutoRAG[gpu]"

install-parse: ## Install AutoRAG with GPU and parsing
	pip install "AutoRAG[gpu,parse]"

install-dev: ## Install development environment (uv)
	uv venv && uv sync --all-extras

setup-nltk: ## Setup NLTK data (required after install)
	pip install --upgrade pyOpenSSL nltk
	$(PYTHON) -c "import nltk; nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"

##@ Code Quality
lint: ## Run ruff linter with auto-fix
	ruff check --fix

format: ## Run ruff formatter
	ruff format

check: ## Run pre-commit hooks on all files
	pre-commit run --all-files

##@ Testing
test-clean: ## Clean up test packages
	$(PYTHON) tests/delete_tests.py

test: test-clean ## Run full test suite
	$(PYTHON) -m pytest -o log_cli=true --log-cli-level=INFO -n auto tests/autorag --timeout 1800

##@ Quick Test (Sample Data)
quick-test: ## Run RAG evaluation with sample data (requires OPENAI_API_KEY)
	autorag evaluate \
		--config $(CONFIG) \
		--qa_data_path $(SAMPLE_QA) \
		--corpus_data_path $(SAMPLE_CORPUS) \
		--project_dir $(PROJECT_DIR)

quick-test-custom: ## Run RAG evaluation with custom LLM server
	autorag evaluate \
		--config $(CONFIG_CUSTOM) \
		--qa_data_path $(SAMPLE_QA) \
		--corpus_data_path $(SAMPLE_CORPUS) \
		--project_dir $(PROJECT_DIR)

##@ RAG Evaluation
evaluate: ## Run RAG evaluation with custom data (qa.parquet, corpus.parquet)
	autorag evaluate \
		--config $(CONFIG) \
		--qa_data_path $(QA_DATA) \
		--corpus_data_path $(CORPUS_DATA) \
		--project_dir $(PROJECT_DIR)

validate: ## Validate config file
	autorag validate \
		--config $(CONFIG) \
		--qa_data_path $(QA_DATA) \
		--corpus_data_path $(CORPUS_DATA) \
		--project_dir $(PROJECT_DIR)

##@ Deployment
dashboard: ## Start result dashboard (port 7690)
	autorag dashboard --trial_dir $(TRIAL_DIR) --port $(DASHBOARD_PORT)

api: ## Start API server (0.0.0.0:8000)
	autorag run_api --trial_dir $(TRIAL_DIR) --host $(API_HOST) --port $(API_PORT)

web: ## Start web interface
	autorag run_web --trial_path $(TRIAL_DIR)

##@ Cleanup
clean: ## Remove trial results and cache
	rm -rf ./0 ./1 ./2 ./logs ./__pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
