# AutoRAG sample_config 설정 파일 가이드

이 문서는 `sample_config/` 폴더의 설정 파일들을 설명하고, 다양한 설정을 변경하여 테스트하는 방법을 안내합니다.

## 목차

1. [폴더 구조 개요](#1-폴더-구조-개요)
2. [Parse 설정 (PDF 파서)](#2-parse-설정-pdf-파서)
3. [Chunk 설정 (문서 청킹)](#3-chunk-설정-문서-청킹)
4. [RAG 설정 (검색 및 생성)](#4-rag-설정-검색-및-생성)
5. [설정 변경하여 테스트하기](#5-설정-변경하여-테스트하기)

---

## 1. 폴더 구조 개요

```text
sample_config/
├── parse/                    # PDF 파싱 설정
│   ├── simple_parse.yaml     # 기본 pdfminer 파서
│   ├── parse_ko.yaml         # 한국어 OCR 파서들
│   ├── parse_ocr.yaml        # OCR 전용 파서들
│   ├── parse_hybird.yaml     # 텍스트+테이블 하이브리드
│   ├── parse_multimodal.yaml # 멀티모달 파서
│   ├── all_files_full.yaml   # 모든 파일 타입 지원
│   └── file_types_full.yaml  # 파일 타입별 파서
│
├── chunk/                    # 문서 청킹 설정
│   ├── simple_chunk.yaml     # 기본 토큰 청킹
│   ├── chunk_ko.yaml         # 한국어 청킹
│   └── chunk_full.yaml       # 모든 청킹 방법
│
└── rag/                      # RAG 파이프라인 설정
    ├── korean/               # 한국어용
    │   ├── gpu/              # GPU 필요 (로컬 모델)
    │   ├── gpu_api/          # GPU + API 혼합
    │   └── non_gpu/          # GPU 불필요 (API만)
    │       ├── simple_korean_custom.yaml   # 커스텀 서버
    │       ├── simple_korean_milvus.yaml   # Milvus VectorDB
    │       ├── simple_korean_weaviate.yaml # Weaviate VectorDB
    │       ├── simple_korean_qdrant.yaml   # Qdrant VectorDB
    │       ├── simple_korean_chroma_http.yaml # Chroma HTTP
    │       └── full_korean.yaml            # 전체 옵션 테스트
    └── english/              # 영어용
        ├── gpu/
        ├── gpu_api/
        └── non_gpu/
```

---

## 2. Parse 설정 (PDF 파서)

### 2.1 사용 가능한 파서 모듈

| 파서 | 모듈 타입 | 특징 | API 키 필요 |
| :--- | :-------- | :--- | :---------- |
| **pdfminer** | `langchain_parse` | 기본 텍스트 추출, 빠름 | 없음 |
| **pdfplumber** | `langchain_parse` | 테이블 추출 우수 | 없음 |
| **unstructured** | `langchain_parse` | 다양한 파일 지원 | 없음 |
| **Upstage** | `langchain_parse` | 한국어 OCR 우수 | `UPSTAGE_API_KEY` |
| **LlamaParse** | `llama_parse` | 멀티모달, 마크다운 출력 | `LLAMA_CLOUD_API_KEY` |
| **Clova OCR** | `clova` | 네이버 OCR, 테이블 인식 | `CLOVA_*` 키들 |

### 2.2 파서별 설정 파일

#### simple_parse.yaml - 기본 파서 (무료)

```yaml
modules:
  - module_type: langchain_parse
    file_type: pdf
    parse_method: pdfminer
```

#### parse_ko.yaml - 한국어 OCR 파서들

```yaml
modules:
  - module_type: llama_parse
    file_type: all_files
    result_type: markdown
    language: ko
  - module_type: clova
    file_type: all_files
    table_detection: true
  - module_type: langchain_parse
    file_type: all_files
    parse_method: upstagedocumentparse
```

#### parse_hybird.yaml - 하이브리드 (텍스트+테이블)

```yaml
modules:
  - module_type: table_hybrid_parse
    file_type: pdf
    text_parse_module: langchain_parse
    text_params:
      parse_method: pdfplumber
    table_parse_module: llamaparse
    table_params:
      result_type: markdown
      language: ko
      use_vendor_multimodal_model: true
      vendor_multimodal_model_name: openai-gpt-4o-mini
```

### 2.3 파서 선택 가이드

| 상황 | 권장 파서 | 이유 |
| :--- | :-------- | :--- |
| 텍스트 위주 PDF | `pdfminer` | 빠르고 무료 |
| 테이블이 많은 PDF | `pdfplumber` 또는 `llama_parse` | 테이블 구조 보존 |
| 스캔된 PDF (이미지) | `clova` 또는 `upstage` | OCR 필요 |
| 복잡한 레이아웃 | `llama_parse` + multimodal | GPT-4o 활용 |
| 한국어 문서 | `clova` 또는 `upstage` | 한국어 OCR 최적화 |

---

## 3. Chunk 설정 (문서 청킹)

### 3.1 사용 가능한 청킹 방법

| 청킹 방법 | 모듈 타입 | 특징 |
| :-------- | :-------- | :--- |
| **Token** | `llama_index_chunk` | 토큰 수 기준 분할 (기본) |
| **Sentence** | `llama_index_chunk` | 문장 단위 분할 |
| **SentenceWindow** | `llama_index_chunk` | 문장 + 주변 문맥 포함 |
| **Semantic** | `llama_index_chunk` | 의미 기반 분할 (임베딩 사용) |
| **SimpleFile** | `llama_index_chunk` | 파일 전체를 하나의 청크로 |
| **RecursiveCharacter** | `langchain_chunk` | 재귀적 문자 분할 |
| **KonlpyTextSplitter** | `langchain_chunk` | 한국어 형태소 기반 분할 |

### 3.2 청킹 설정 파일

#### simple_chunk.yaml - 기본 토큰 청킹

```yaml
modules:
  - module_type: llama_index_chunk
    chunk_method: Token
```

#### chunk_ko.yaml - 한국어 청킹 (다양한 방법 비교)

```yaml
modules:
  # 토큰/문장 기반 (청크 크기 비교)
  - module_type: llama_index_chunk
    chunk_method: [ Token, Sentence ]
    chunk_size: [ 1024, 512 ]
    chunk_overlap: 24
    add_file_name: ko

  # 문장 윈도우 (주변 문맥 포함)
  - module_type: llama_index_chunk
    chunk_method: [ SentenceWindow ]
    sentence_splitter: kiwi    # 한국어 형태소 분석기
    add_file_name: ko

  # 의미 기반 청킹
  - module_type: llama_index_chunk
    chunk_method: [ Semantic_llama_index ]
    embed_model: openai
    add_file_name: ko

  # 한국어 형태소 기반
  - module_type: langchain_chunk
    chunk_method: KonlpyTextSplitter
```

### 3.3 청킹 파라미터 설명

| 파라미터 | 설명 | 기본값 | 권장값 |
| :------- | :--- | :----- | :----- |
| `chunk_size` | 청크 크기 (토큰 수) | 512 | 256~1024 |
| `chunk_overlap` | 청크 간 겹침 | 50 | chunk_size의 10% |
| `add_file_name` | 청크에 파일명 추가 | - | `ko` 또는 `en` |
| `sentence_splitter` | 문장 분리기 | - | `kiwi` (한국어) |

### 3.4 청킹 선택 가이드

| 상황 | 권장 청킹 | 이유 |
| :--- | :-------- | :--- |
| 일반적인 문서 | `Token` (512) | 균일한 크기, 빠른 처리 |
| 긴 문서, 문맥 중요 | `SentenceWindow` | 주변 문맥 보존 |
| 의미 단위 분리 필요 | `Semantic` | 의미적으로 관련된 내용 유지 |
| 한국어 문서 | `KonlpyTextSplitter` | 형태소 경계 고려 |
| FAQ 형식 | `SimpleFile` | 각 파일이 하나의 답변 |

---

## 4. RAG 설정 (검색 및 생성)

### 4.1 RAG 파이프라인 구조

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG 파이프라인                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Query] ──→ [Query Expansion] ──→ [Retrieval] ──→ [Reranking]     │
│                    (선택)              │              (선택)        │
│                                        ↓                           │
│              [Prompt Maker] ←── [Retrieved Docs]                   │
│                    │                                               │
│                    ↓                                               │
│              [Generator] ──→ [Answer]                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 RAG 설정 파일 비교

| 파일 | 복잡도 | 용도 |
| :--- | :----: | :--- |
| `simple_korean_custom.yaml` | 낮음 | 빠른 테스트, 커스텀 서버 |
| `simple_korean_milvus.yaml` | 낮음 | Milvus VectorDB 테스트 |
| `compact_korean.yaml` | 중간 | 주요 옵션 비교 |
| `half_korean.yaml` | 중간 | 절반 옵션 테스트 |
| `full_korean.yaml` | 높음 | 모든 옵션 완전 탐색 |

### 4.3 VectorDB 설정

#### Chroma (로컬, 기본)

```yaml
vectordb:
  - name: custom_vectordb
    db_type: chroma
    client_type: persistent
    path: ${PROJECT_DIR}/logs/chroma
    collection_name: custom_collection
    embedding_batch: 100
    embedding_model:
      - type: openai_like
        model_name: ${CUSTOM_EMBEDDING_MODEL}
        api_base: ${CUSTOM_EMBEDDING_API_BASE}
```

#### Milvus (분산 처리용)

```yaml
vectordb:
  - name: milvus_vectordb
    db_type: milvus
    uri: http://${MILVUS_HOST}:${MILVUS_PORT}
    user: ${MILVUS_USER}
    password: ${MILVUS_PASSWORD}
    collection_name: ${MILVUS_COLLECTION_NAME}
    similarity_metric: cosine
    index_type: AUTOINDEX
    embedding_model:
      - type: openai_like
        model_name: ${CUSTOM_EMBEDDING_MODEL}
        api_base: ${CUSTOM_EMBEDDING_API_BASE}
```

#### Weaviate

```yaml
vectordb:
  - name: weaviate_vectordb
    db_type: weaviate
    host: ${WEAVIATE_HOST}
    port: ${WEAVIATE_PORT}
    grpc_port: ${WEAVIATE_GRPC_PORT}
    collection_name: autorag_collection
    embedding_model:
      - type: openai_like
        model_name: ${CUSTOM_EMBEDDING_MODEL}
        api_base: ${CUSTOM_EMBEDDING_API_BASE}
```

#### Qdrant

```yaml
vectordb:
  - name: qdrant_vectordb
    db_type: qdrant
    host: ${QDRANT_HOST}
    port: ${QDRANT_PORT}
    collection_name: autorag_collection
    embedding_model:
      - type: openai_like
        model_name: ${CUSTOM_EMBEDDING_MODEL}
        api_base: ${CUSTOM_EMBEDDING_API_BASE}
```

### 4.4 검색 노드 설정

#### 기본 의미 검색 (Semantic Retrieval)

```yaml
- node_type: semantic_retrieval
  strategy:
    metrics:
      - retrieval_f1
      - retrieval_recall
      - retrieval_precision
  top_k: 3
  modules:
    - module_type: vectordb
      vectordb: custom_vectordb
```

#### BM25 키워드 검색 (Lexical Retrieval)

```yaml
- node_type: lexical_retrieval
  strategy:
    metrics: [ retrieval_f1, retrieval_recall, retrieval_precision ]
  top_k: 10
  modules:
    - module_type: bm25
      bm25_tokenizer: [ ko_kiwi, ko_okt, ko_kkma ]  # 한국어 토크나이저
```

#### 하이브리드 검색 (BM25 + Vector)

```yaml
- node_type: hybrid_retrieval
  strategy:
    metrics: [ retrieval_f1, retrieval_recall, retrieval_precision ]
  top_k: 10
  modules:
    - module_type: hybrid_rrf    # Reciprocal Rank Fusion
      weight_range: (4, 80)
    - module_type: hybrid_cc     # Convex Combination
      normalize_method: [ mm, tmm, z, dbsf ]
      weight_range: (0.0, 1.0)
```

### 4.5 생성 노드 설정

#### 프롬프트 생성기

```yaml
- node_type: prompt_maker
  strategy:
    metrics:
      - bleu
      - meteor
      - rouge
  modules:
    - module_type: chat_fstring
      prompt:
        - - role: system
            content: "주어진 passage만을 이용하여 질문에 답하시오."
          - role: user
            content: "passage: {retrieved_contents}\n\nQuestion: {query}\n\nAnswer:"
```

#### LLM 생성기

```yaml
- node_type: generator
  strategy:
    metrics:
      - metric_name: rouge
  modules:
    - module_type: llama_index_llm
      llm: openailike
      model: ${CUSTOM_LLM_MODEL}
      api_base: ${CUSTOM_LLM_API_BASE}
      api_key: ${CUSTOM_LLM_API_KEY}
      is_chat_model: true
      temperature: 0.1
      max_tokens: 4096
```

---

## 5. 설정 변경하여 테스트하기

### 5.1 방법 1: 새 테스트 케이스 생성

`scripts/test-config.yaml`에 새 테스트 케이스를 추가합니다.

```yaml
test_cases:
  # 기존 케이스...

  # 새로운 테스트 케이스 추가
  hr_rule_llama_parse:
    description: "인사규정 - LlamaParse 파서 테스트"
    input_dir: "docs/sample-data/인사규정"
    output_dir: "logs/testCase/hr_rule_llama_parse"
    rag_config: "sample_config/rag/korean/non_gpu/simple_korean_milvus.yaml"
    # 청크 설정은 기본값 사용
```

실행:

```bash
make run-testcase TESTCASE=hr_rule_llama_parse
```

### 5.2 방법 2: prepare_custom_data.py 수정

`scripts/prepare_custom_data.py`의 설정 함수를 수정합니다.

#### PDF 파서 변경

```python
def create_parse_config(output_dir: str) -> str:
    """파싱 설정 YAML 파일 생성"""
    # 기본: pdfminer
    # config_content = """modules:
    #   - module_type: langchain_parse
    #     file_type: pdf
    #     parse_method: pdfminer
    # """

    # 변경: LlamaParse (마크다운 출력)
    config_content = """modules:
  - module_type: llama_parse
    file_type: pdf
    result_type: markdown
    language: ko
"""
    # ...
```

#### 청킹 방법 변경

```python
def create_chunk_config(output_dir: str, chunk_size: int = 512, chunk_overlap: int = 50) -> str:
    """청킹 설정 YAML 파일 생성"""
    # 기본: Token 청킹
    # config_content = f"""modules:
    #   - module_type: llama_index_chunk
    #     chunk_method: Token
    #     chunk_size: {chunk_size}
    #     chunk_overlap: {chunk_overlap}
    #     add_file_name: ko
    # """

    # 변경: Semantic 청킹
    config_content = f"""modules:
  - module_type: llama_index_chunk
    chunk_method: Semantic_llama_index
    embed_model: openai
    add_file_name: ko
"""
    # ...
```

### 5.3 방법 3: RAG 설정 파일 복사 후 수정

```bash
# 1. 기존 설정 복사
cp sample_config/rag/korean/non_gpu/simple_korean_milvus.yaml \
   sample_config/rag/korean/non_gpu/my_custom_rag.yaml

# 2. 파일 수정 (예: top_k 변경, 프롬프트 수정 등)

# 3. 테스트 케이스에서 새 설정 사용
# scripts/test-config.yaml:
#   my_test:
#     rag_config: "sample_config/rag/korean/non_gpu/my_custom_rag.yaml"
```

### 5.4 예제: 다양한 설정 비교 테스트

#### 청크 크기 비교

```yaml
# scripts/test-config.yaml
test_cases:
  hr_chunk_256:
    description: "인사규정 - chunk_size=256"
    input_dir: "docs/sample-data/인사규정"
    output_dir: "logs/testCase/hr_chunk_256"
    chunk_size: 256
    chunk_overlap: 25

  hr_chunk_512:
    description: "인사규정 - chunk_size=512"
    input_dir: "docs/sample-data/인사규정"
    output_dir: "logs/testCase/hr_chunk_512"
    chunk_size: 512
    chunk_overlap: 50

  hr_chunk_1024:
    description: "인사규정 - chunk_size=1024"
    input_dir: "docs/sample-data/인사규정"
    output_dir: "logs/testCase/hr_chunk_1024"
    chunk_size: 1024
    chunk_overlap: 100
```

```bash
# 순차 실행
make run-testcase TESTCASE=hr_chunk_256
make run-testcase TESTCASE=hr_chunk_512
make run-testcase TESTCASE=hr_chunk_1024

# 결과 비교
make compare-results
```

#### VectorDB 비교 (현재 구현됨)

```bash
make run-testcase TESTCASE=hr_rule_milvus
make run-testcase TESTCASE=hr_rule_weaviate
make run-testcase TESTCASE=hr_rule_qdrant
make compare-results
```

---

## 6. 환경변수 설정 (.env)

테스트에 필요한 환경변수들입니다.

```bash
# LLM 서버
CUSTOM_LLM_API_BASE=https://llmserving.example.com/v1
CUSTOM_LLM_MODEL=openai/gpt-oss-120b
CUSTOM_LLM_API_KEY=

# 임베딩 서버
CUSTOM_EMBEDDING_API_BASE=http://localhost:8081
CUSTOM_EMBEDDING_MODEL=BAAI/bge-m3

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=
MILVUS_COLLECTION_NAME=autorag_collection

# Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Chroma HTTP
CHROMA_HOST=localhost
CHROMA_PORT=8000

# 유료 파서 API 키 (선택)
LLAMA_CLOUD_API_KEY=llx-xxxx
UPSTAGE_API_KEY=up_xxxx
CLOVA_SECRET_KEY=xxxx
CLOVA_APIGW_API_KEY=xxxx
CLOVA_OCR_URL=https://xxxx.apigw.ntruss.com/xxxx
```

---

## 7. 주요 명령어 요약

| 명령어 | 설명 |
| :----- | :--- |
| `make list-testcases` | 테스트 케이스 목록 |
| `make show-testcase TESTCASE=<name>` | QA 데이터 확인 |
| `make run-testcase TESTCASE=<name>` | 전체 워크플로우 실행 |
| `make prepare-data TESTCASE=<name>` | 데이터 준비만 |
| `make evaluate-custom TESTCASE=<name>` | 평가만 실행 |
| `make compare-results` | 결과 비교 |
| `make dashboard TRIAL_DIR=<path>` | 대시보드 실행 |

---

## 8. 참고 자료

- [AutoRAG 공식 문서](https://docs.auto-rag.com/)
- [LlamaIndex Chunking](https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/)
- [LangChain Document Loaders](https://python.langchain.com/docs/modules/data_connection/document_loaders/)
