# 온프레미스 PDF 파서 추가 (Marker, Docling)

## 배경

LlamaParse는 클라우드 API 기반으로 `LLAMA_CLOUD_API_KEY`가 필요합니다.
온프레미스 RAG 구축을 위해 로컬에서 실행 가능한 파서들을 추가했습니다.

## 변경 사항

### 1. Makefile - 설치 타겟 추가

```bash
make install-onpremise  # marker-pdf, docling 설치
```

### 2. 새로운 파서 모듈 추가

| 파일 | 설명 |
|------|------|
| `autorag/data/parse/marker_parse.py` | Marker PDF 파서 |
| `autorag/data/parse/docling_parse.py` | Docling (IBM) PDF 파서 |

### 3. 파서 등록

- `autorag/support.py` - 모듈 등록
- `autorag/data/parse/base.py` - wrapper 함수에 추가
- `autorag/data/parse/__init__.py` - export 추가

### 4. Parse Config 파일 추가

| 파일 | 설명 |
|------|------|
| `sample_config/parse/parse_marker.yaml` | Marker 단독 사용 |
| `sample_config/parse/parse_docling.yaml` | Docling 단독 사용 |
| `sample_config/parse/parse_onpremise.yaml` | 3가지 파서 비교 |

### 5. 테스트 케이스 변경 (`scripts/test-config.yaml`)

**제거:**
- `hr_rule_hybrid_chunk_ko` (LlamaParse 의존)

**추가:**
- `hr_rule_marker` - Marker 파서 테스트
- `hr_rule_docling` - Docling 파서 테스트
- `hr_rule_onpremise_compare` - 3가지 파서 비교 (Marker vs Docling vs pdfplumber)

## 사용법

```bash
# 1. 온프레미스 파서 설치
make install-onpremise

# 2. 테스트 실행
make run-testcase TESTCASE=hr_rule_marker
make run-testcase TESTCASE=hr_rule_docling
make run-testcase TESTCASE=hr_rule_onpremise_compare
```

## 파서 비교

| 파서 | 장점 | 단점 |
|------|------|------|
| **Marker** | 마크다운 변환 우수, 테이블 지원 | GPU 권장 |
| **Docling** (IBM) | 구조화된 콘텐츠 추출 우수 | 속도 느림 |
| **pdfplumber** | 빠름, 가벼움 | 테이블 지원 제한적 |

## 참고

- Marker: https://github.com/VikParuchuri/marker
- Docling: https://github.com/DS4SD/docling
