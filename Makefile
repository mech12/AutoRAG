.PHONY: help install install-dev setup-nltk lint format check test test-clean \
        quick-test quick-test-custom prepare-data evaluate evaluate-custom \
        help-prepare-data help-evaluate-custom dashboard api web validate clean

# Default target
.DEFAULT_GOAL := help

# Load environment variables from .env file (if exists)
-include .env
export

# Variables
VENV := .venv
PYTHON := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python)
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

quick-test-custom: ## Run RAG evaluation with custom LLM server (requires .env)
	@if [ ! -f .env ]; then echo "Error: .env file not found. Copy .env.example to .env first."; exit 1; fi
	autorag evaluate \
		--config $(CONFIG_CUSTOM) \
		--qa_data_path $(SAMPLE_QA) \
		--corpus_data_path $(SAMPLE_CORPUS) \
		--project_dir $(PROJECT_DIR)

##@ Data Preparation
prepare-data: ## Prepare custom PDF data for evaluation (requires input_dir)
	@if [ -z "$(INPUT_DIR)" ]; then echo "Usage: make prepare-data INPUT_DIR=/path/to/pdfs [OUTPUT_DIR=data/custom] [NUM_QA=20] [USE_LLM=false]"; exit 1; fi
	$(PYTHON) scripts/prepare_custom_data.py \
		--input_dir $(INPUT_DIR) \
		--output_dir $(or $(OUTPUT_DIR),data/custom) \
		--num_qa $(or $(NUM_QA),20) \
		$(if $(filter true,$(USE_LLM)),--use_llm,)

help-prepare-data: ## Show detailed help for prepare-data
	@echo ""
	@echo "\033[1m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
	@echo "\033[1m  prepare-data: PDF를 AutoRAG 평가용 데이터셋으로 변환\033[0m"
	@echo "\033[1m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
	@echo ""
	@echo "\033[33m사용법:\033[0m"
	@echo "  make prepare-data INPUT_DIR=<pdf_directory> [OPTIONS]"
	@echo ""
	@echo "\033[33m필수 파라미터:\033[0m"
	@echo "  \033[36mINPUT_DIR\033[0m      PDF 파일이 있는 디렉토리 경로"
	@echo ""
	@echo "\033[33m선택 파라미터:\033[0m"
	@echo "  \033[36mOUTPUT_DIR\033[0m     출력 디렉토리 (기본값: data/custom)"
	@echo "  \033[36mNUM_QA\033[0m         생성할 QA 쌍 개수 (기본값: 20)"
	@echo "  \033[36mUSE_LLM\033[0m        LLM으로 고품질 QA 생성 (true/false, 기본값: false)"
	@echo ""
	@echo "\033[33m예제:\033[0m"
	@echo "  # 기본 사용 (LLM 없이 빠른 테스트)"
	@echo "  make prepare-data INPUT_DIR=docs/sample-data"
	@echo ""
	@echo "  # LLM 사용하여 고품질 QA 생성"
	@echo "  make prepare-data INPUT_DIR=docs/sample-data USE_LLM=true NUM_QA=50"
	@echo ""
	@echo "  # 출력 디렉토리 지정"
	@echo "  make prepare-data INPUT_DIR=/path/to/pdfs OUTPUT_DIR=data/my_dataset"
	@echo ""
	@echo "\033[33m처리 단계:\033[0m"
	@echo "  1. PDF 파싱    - pdfminer로 텍스트 추출"
	@echo "  2. 문서 청킹   - 512 토큰 단위로 분할 (50 토큰 오버랩)"
	@echo "  3. QA 생성     - 질문-답변 쌍 생성"
	@echo ""
	@echo "\033[33m생성되는 파일:\033[0m"
	@echo "  OUTPUT_DIR/"
	@echo "  ├── corpus.parquet    # 청킹된 문서 코퍼스"
	@echo "  ├── qa.parquet        # 질문-답변 데이터셋"
	@echo "  ├── parse_config.yaml # 파싱 설정"
	@echo "  └── chunk_config.yaml # 청킹 설정"
	@echo ""
	@echo "\033[33m다음 단계:\033[0m"
	@echo "  make evaluate-custom  # 생성된 데이터로 RAG 평가 실행"
	@echo ""

##@ RAG Evaluation
evaluate: ## Run RAG evaluation with custom data (qa.parquet, corpus.parquet)
	autorag evaluate \
		--config $(CONFIG) \
		--qa_data_path $(QA_DATA) \
		--corpus_data_path $(CORPUS_DATA) \
		--project_dir $(PROJECT_DIR)

evaluate-custom: ## Run RAG evaluation with prepared custom data (data/custom/)
	@if [ ! -f .env ]; then echo "Error: .env file not found. Copy .env.example to .env first."; exit 1; fi
	@if [ ! -f data/custom/qa.parquet ]; then echo "Error: data/custom/qa.parquet not found. Run 'make prepare-data' first."; exit 1; fi
	autorag evaluate \
		--config $(CONFIG_CUSTOM) \
		--qa_data_path data/custom/qa.parquet \
		--corpus_data_path data/custom/corpus.parquet \
		--project_dir $(PROJECT_DIR)

help-evaluate-custom: ## Show detailed help for evaluate-custom
	@echo ""
	@echo "\033[1m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
	@echo "\033[1m  evaluate-custom: 커스텀 LLM/임베딩 서버로 RAG 평가 실행\033[0m"
	@echo "\033[1m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
	@echo ""
	@echo "\033[33m사용법:\033[0m"
	@echo "  make evaluate-custom"
	@echo ""
	@echo "\033[33m사전 요구사항:\033[0m"
	@echo "  1. .env 파일 설정 (cp .env.example .env)"
	@echo "  2. data/custom/ 데이터 준비 (make prepare-data)"
	@echo ""
	@echo "\033[33m환경변수 (.env):\033[0m"
	@echo "  \033[36mCUSTOM_LLM_API_BASE\033[0m       LLM 서버 URL"
	@echo "                            예: https://llmserving.surromind.ai/v1"
	@echo "  \033[36mCUSTOM_LLM_MODEL\033[0m          LLM 모델명"
	@echo "                            예: openai/gpt-oss-120b"
	@echo "  \033[36mCUSTOM_EMBEDDING_API_BASE\033[0m 임베딩 서버 URL"
	@echo "                            예: http://10.10.20.94:8081"
	@echo "  \033[36mCUSTOM_EMBEDDING_MODEL\033[0m    임베딩 모델명"
	@echo "                            예: BAAI/bge-m3"
	@echo ""
	@echo "\033[33m평가 파이프라인:\033[0m"
	@echo "  ┌─────────────────┐    ┌──────────────┐    ┌────────────┐"
	@echo "  │ Semantic Search │ -> │ Prompt Maker │ -> │ Generator  │"
	@echo "  │   (BGE-M3)      │    │ (ChatFstring)│    │ (OpenAI)   │"
	@echo "  └─────────────────┘    └──────────────┘    └────────────┘"
	@echo ""
	@echo "\033[33m평가 메트릭:\033[0m"
	@echo "  - Retrieval: F1, Recall, Precision"
	@echo "  - Generation: ROUGE Score"
	@echo ""
	@echo "\033[33m결과 파일:\033[0m"
	@echo "  logs/"
	@echo "  ├── 0/                    # Trial 결과"
	@echo "  │   ├── summary.csv       # 최적 파이프라인 요약"
	@echo "  │   ├── config.yaml       # 사용된 설정"
	@echo "  │   └── *_node_line/      # 각 노드별 상세 결과"
	@echo "  └── trial.json            # Trial 메타데이터"
	@echo ""
	@echo "\033[33m결과 확인:\033[0m"
	@echo "  make dashboard            # 대시보드 실행 (http://localhost:7690)"
	@echo "  cat logs/0/summary.csv    # 요약 결과 확인"
	@echo ""
	@echo "\033[33m문제 해결:\033[0m"
	@echo "  - doc_id not found 오류: rm -rf logs/ 후 재실행"
	@echo "  - 연결 오류: .env 파일의 서버 URL 확인"
	@echo ""

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
