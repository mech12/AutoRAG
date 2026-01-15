# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

## 2026-01-15

### Changed

- **Compare Web 탭 이름을 QA Test로 변경** (`scripts/compare_web.py`)
  - 탭 이름 "Compare Web" → "QA Test"로 변경
  - 관련 문서 업데이트
- **코드 포맷팅 개선** (`scripts/compare_web.py`)
  - ruff format 적용
  - trailing comma 추가

## 2026-01-13

### Fixed

- **Chroma HTTP 클라이언트 호환성 수정** (`autorag/vectordb/chroma.py`)
  - chromadb 1.0+ 에서 `AsyncHttpClient`가 코루틴을 반환하는 문제 해결
  - 동기 컨텍스트에서 사용 가능하도록 `HttpClient`로 변경
- **Vector DB doc_id 불일치 에러 수정** (`scripts/run_evaluation.py`)
  - 평가 전 기존 컬렉션 자동 삭제로 stale doc_id 문제 방지
  - Milvus, Weaviate, Qdrant, Chroma HTTP 모두 지원

### Added

- **Vector DB 비교 테스트 케이스** (`scripts/test-config.yaml`)
  - 인사규정 기준: `hr_rule_milvus`, `hr_rule_weaviate`, `hr_rule_qdrant`, `hr_rule_chroma_http`
  - 고압가스 기준: `gas_safety_milvus`, `gas_safety_weaviate`, `gas_safety_qdrant`, `gas_safety_chroma_http`
- **Milvus 동적 컬렉션 이름 생성**
  - `MILVUS_COLLECTION_NAME_PREFIX` 환경변수 지원
  - 테스트케이스별 자동 생성: `{prefix}_autorag_{testcase_name}`
  - 한글 테스트케이스명 자동 로마자 변환 (인사규정 → insa, 고압가스 → gas)
- **Chroma HTTP 컬렉션 자동 삭제** (`_delete_chroma_collection_if_exists`)
- **외부 parse/chunk 설정 파일 지원**
  - 테스트케이스에서 `parse_config`, `chunk_config` 필드로 외부 YAML 참조
  - 예: `hr_rule_hybrid_chunk_ko` (LlamaParse + 한국어 청킹)

### Changed

- **`make list-testcases` 출력 간소화**
  - `make run-testcase TESTCASE=...` 명령만 표시
  - 불필요한 `prepare-data`, `evaluate-custom` 명령 제거

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
