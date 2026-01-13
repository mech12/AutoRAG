# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Fixed

- Fix doc_id mismatch error in VectorDB after validation
  - Validation creates sample data in collections which caused doc_id not found errors
  - Added automatic VectorDB collection cleanup after validation completes
  - Supports Weaviate, Milvus, Qdrant, and Chroma cleanup
- Fix Chroma HTTP client: Change AsyncHttpClient to HttpClient for compatibility

### Added

- Add `make show-testcase TESTCASE=<name>` command to display QA data
- Add documentation for QA generation methods and test results
- Add comprehensive sample_config guide (parse, chunk, RAG settings)
- Add support for external parse_config and chunk_config in test cases
  - New testcase fields: `parse_config`, `chunk_config`
  - Example: `hr_rule_hybrid_chunk_ko` using `parse_hybird.yaml` + `chunk_ko.yaml`

## 2026-01-08

### Installation (Server: Ubuntu 24.04, Python 3.12.3)

UV 패키지 매니저를 사용하여 AutoRAG 설치 완료.

#### 설치 환경
- **OS**: Linux 6.14.0-35-generic (Ubuntu)
- **Python**: 3.12.3
- **UV**: 0.9.22

#### 설치 명령어
```bash
# UV 설치
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# AutoRAG 설치
cd /home/surromind/kb/AutoRAG
uv venv && source .venv/bin/activate
uv pip install -r pyproject.toml --all-extras -e .
```

#### 설치된 주요 패키지 (434개)
- autorag==0.0.1
- torch==2.9.0
- vllm==0.13.0
- transformers==4.57.3
- langchain==0.2.17
- llama-index==0.14.12
- chromadb==1.4.0
- openai==1.109.1
- anthropic==0.71.0

#### 확인
```bash
autorag --help
```
