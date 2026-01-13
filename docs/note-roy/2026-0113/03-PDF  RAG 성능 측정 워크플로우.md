# PDF RAG 성능 측정 워크플로우

커스텀 PDF 데이터를 사용하여 AutoRAG로 RAG 파이프라인 성능을 측정하는 방법을 설명합니다.

## 샘플 데이터

```text
docs/sample-data/
└── 인사규정-07-취업규칙.pdf
```

## 빠른 시작

```bash
# 1단계: PDF 데이터 준비 (LLM 없이)
make prepare-data INPUT_DIR=docs/sample-data

# 2단계: RAG 평가 실행
make evaluate-custom
```

## 상세 워크플로우

### 1. 데이터 준비 옵션

| 옵션 | 설명 | 기본값 |
| ---- | ---- | ------ |
| `INPUT_DIR` | PDF 파일이 있는 디렉토리 (필수) | - |
| `OUTPUT_DIR` | 출력 디렉토리 | `data/custom` |
| `NUM_QA` | 생성할 QA 쌍 개수 | `20` |
| `USE_LLM` | LLM으로 고품질 QA 생성 | `false` |

```bash
# LLM 없이 빠른 테스트용 QA 생성
make prepare-data INPUT_DIR=docs/sample-data

# LLM 사용하여 고품질 QA 생성 (.env 설정 필요)
make prepare-data INPUT_DIR=docs/sample-data USE_LLM=true NUM_QA=50
```

### 2. 생성되는 파일

```text
data/custom/
├── parsed_result.parquet  # PDF 파싱 결과 (원본 텍스트)
├── corpus.parquet         # 청킹된 문서 코퍼스
└── qa.parquet             # 질문-답변 데이터셋
```

### 3. 처리 단계

| 단계 | 설명 | 세부사항 |
| ---- | ---- | -------- |
| PDF 파싱 | PDF → 텍스트 변환 | pdfminer 사용 |
| 문서 청킹 | 텍스트 분할 | 512 토큰, 50 토큰 오버랩 |
| QA 생성 | 질문-답변 쌍 생성 | LLM 또는 규칙 기반 |

### 4. 평가 실행

```bash
# 커스텀 데이터로 평가
make evaluate-custom

# 또는 직접 명령어 실행
autorag evaluate \
    --config sample_config/rag/korean/non_gpu/simple_korean_custom.yaml \
    --qa_data_path data/custom/qa.parquet \
    --corpus_data_path data/custom/corpus.parquet \
    --project_dir logs
```

### 5. 결과 확인

```bash
# 대시보드 실행
make dashboard

# 브라우저에서 http://localhost:7690 접속
```

## 환경 설정

`.env` 파일이 필요합니다. `.env.example`을 복사하여 설정하세요:

```bash
cp .env.example .env
```

### 필수 환경변수

| 변수 | 설명 | 예시 |
| ---- | ---- | ---- |
| `CUSTOM_LLM_API_BASE` | LLM 서버 URL | `https://llmserving.surromind.ai/v1` |
| `CUSTOM_LLM_MODEL` | LLM 모델명 | `openai/gpt-oss-120b` |
| `CUSTOM_EMBEDDING_API_BASE` | 임베딩 서버 URL | `http://10.10.20.94:8081` |
| `CUSTOM_EMBEDDING_MODEL` | 임베딩 모델명 | `BAAI/bge-m3` |

## 스크립트 직접 사용

`scripts/prepare_custom_data.py`를 직접 실행할 수도 있습니다:

```bash
python scripts/prepare_custom_data.py \
    --input_dir docs/sample-data \
    --output_dir data/custom \
    --num_qa 20 \
    --use_llm  # LLM 사용 시

# 옵션
#   --skip_parse  : 이미 파싱된 결과가 있으면 건너뛰기
#   --skip_qa     : QA 생성 없이 파싱/청킹만 수행
```

## 문제 해결

### PDF 파싱 오류

- `pdfminer`가 설치되어 있는지 확인: `pip install pdfminer.six`
- 한글 PDF의 경우 인코딩 문제가 있을 수 있음

### LLM 연결 오류

- `.env` 파일의 `CUSTOM_LLM_API_BASE` URL 확인
- 서버 연결 상태 확인: `curl $CUSTOM_LLM_API_BASE/models`

### 메모리 부족

- `NUM_QA` 값을 줄여서 테스트
- 청크 크기 조정 (스크립트 내 `chunk_size` 파라미터)
