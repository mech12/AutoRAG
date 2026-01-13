# AutoRAG 테스트 결과 분석

이 문서는 AutoRAG 평가 결과를 초보자 관점에서 자세히 설명합니다.

## 1. Vector DB 비교 결과 요약

### 전체 성능 비교표

| 테스트 케이스       | 설명                                      | F1    | Recall | Precision | ROUGE | 실행시간 |
| :------------------ | :---------------------------------------- | :---: | :----: | :-------: | :---: | :------: |
| hr_rule_docling     | Docling 파서 (온프레미스, IBM)            | 0.500 | 1.00   | 0.333     | 0.357 | 1.49s    |
| hr_rule_milvus      | Milvus Vector DB                          | 0.475 | 0.95   | 0.317     | 0.420 | 1.61s    |
| hr_rule_weaviate    | Weaviate Vector DB                        | 0.475 | 0.95   | 0.317     | 0.392 | 1.45s    |
| hr_rule_qdrant      | Qdrant Vector DB                          | 0.475 | 0.95   | 0.317     | 0.415 | 1.29s    |
| hr_rule_chroma_http | Chroma HTTP Vector DB                     | 0.475 | 0.95   | 0.317     | 0.416 | 1.43s    |

### 주요 발견

- **Docling 파서가 검색 성능 최고**: F1 0.500, Recall 100% (다른 파서 대비 5% 향상)
- **검색 성능 (Vector DB 비교)**: 4개 Vector DB 모두 **동일한 검색 성능**을 보임 (F1: 0.475)
- **생성 품질 (ROUGE)**: Milvus(0.420) > Chroma(0.416) > Qdrant(0.415) > Weaviate(0.392) > Docling(0.357)
- **실행 속도**: Qdrant(1.29s) > Chroma(1.43s) > Weaviate(1.45s) > Docling(1.49s) > Milvus(1.61s)

### 파서 vs Vector DB 영향 분석

| 구분 | 검색 성능 영향 | 생성 품질 영향 |
| :--- | :------------- | :------------- |
| **파서 변경** (Docling) | F1 +5% 향상 | ROUGE -6% 하락 |
| **Vector DB 변경** | 변화 없음 | ROUGE ±3% 변동 |

> Docling 파서는 검색 성능은 높지만, 생성 품질(ROUGE)이 낮은 이유는 파싱된 텍스트 형식이 LLM 답변 생성에 최적화되지 않았기 때문으로 추정됨

### 테스트 케이스별 설정 상세

| 테스트 케이스       | 파서           | 청킹 설정                | Vector DB        |
| :------------------ | :------------- | :----------------------- | :--------------- |
| hr_rule_docling     | Docling        | chunk_ko_onpremise.yaml  | Chroma (로컬)    |
| hr_rule_milvus      | pdfplumber     | 기본값 (512/50)          | Milvus           |
| hr_rule_weaviate    | pdfplumber     | 기본값 (512/50)          | Weaviate         |
| hr_rule_qdrant      | pdfplumber     | 기본값 (512/50)          | Qdrant           |
| hr_rule_chroma_http | pdfplumber     | 기본값 (512/50)          | Chroma (HTTP)    |

#### hr_rule_docling 청킹 설정 (`chunk_ko_onpremise.yaml`)

```yaml
modules:
  - module_type: llama_index_chunk
    chunk_method: [ Token, Sentence ]
    chunk_size: [ 1024, 512 ]
    chunk_overlap: 24
    add_file_name: ko
  - module_type: llama_index_chunk
    chunk_method: [ SentenceWindow ]
    sentence_splitter: kiwi
    add_file_name: ko
  - module_type: llama_index_chunk
    chunk_method: [ SimpleFile ]
    add_file_name: ko
```

| 청킹 방법        | 설정                  | 설명                     |
| :--------------- | :-------------------- | :----------------------- |
| Token            | 1024, 512 토큰        | 토큰 단위로 분할         |
| Sentence         | 1024, 512 토큰        | 문장 경계 기준 분할      |
| SentenceWindow   | kiwi 형태소 분석기    | 한국어 문장 윈도우       |
| SimpleFile       | -                     | 파일 전체를 하나의 청크  |

#### 기본 청킹 설정 (hr_rule_milvus 등)

```yaml
chunk_size: 512
chunk_overlap: 50
```

## 2. 각 지표(Metric)의 의미

### 2.1 검색 성능 지표 (Retrieval Metrics)

RAG 시스템에서 **검색**은 질문과 관련된 문서를 찾는 단계입니다.

#### retrieval_recall (재현율) = 0.95

```text
                    실제로 찾은 정답 문서 수
재현율(Recall) = ─────────────────────────────
                    전체 정답 문서 수
```

**쉬운 설명**:

- "정답 문서 10개 중에서 몇 개를 찾았나?"
- 0.95 = 95% → 정답 문서 10개 중 9.5개를 찾음
- **높을수록 좋음** (놓치는 정답이 적음)

**예시**:

```text
질문: "연차휴가는 몇 일인가요?"
정답 문서: [문서A, 문서B] (2개)
검색 결과: [문서A, 문서B, 문서C] (3개)

→ 정답 2개 중 2개를 찾음 = Recall 100%
```

#### retrieval_precision (정밀도) = 0.317

```text
                      실제로 찾은 정답 문서 수
정밀도(Precision) = ─────────────────────────────
                      검색된 전체 문서 수
```

**쉬운 설명**:

- "검색된 문서 중에서 실제 정답은 몇 개인가?"
- 0.317 = 31.7% → 검색된 3개 문서 중 약 1개만 정답
- **높을수록 좋음** (쓸데없는 문서가 적음)

**예시**:

```text
질문: "연차휴가는 몇 일인가요?"
검색 결과: [문서A, 문서B, 문서C] (3개)
이 중 정답: [문서A] (1개)

→ 검색 3개 중 정답 1개 = Precision 33%
```

#### retrieval_f1 (F1 점수) = 0.475

```text
           2 × Precision × Recall
F1 점수 = ─────────────────────────
           Precision + Recall
```

**쉬운 설명**:

- Recall과 Precision의 **조화 평균**
- 두 지표를 균형있게 평가
- 0.475 = 47.5% → 검색 성능이 중간 정도

**왜 F1을 사용하나?**

```text
Case 1: Recall 100%, Precision 10%
  → 모든 문서를 다 가져오면 정답은 다 찾지만 쓸데없는 것도 많음

Case 2: Recall 10%, Precision 100%
  → 확실한 것만 가져오면 정확하지만 놓치는 정답이 많음

F1은 이 둘의 균형을 측정
```

### 2.2 생성 성능 지표 (Generation Metrics)

RAG 시스템에서 **생성**은 검색된 문서를 바탕으로 답변을 만드는 단계입니다.

#### rouge = 0.392 ~ 0.42

**ROUGE (Recall-Oriented Understudy for Gisting Evaluation)**

```text
              생성된 답변과 정답이 겹치는 단어 수
ROUGE 점수 = ─────────────────────────────────────
              정답의 전체 단어 수
```

**쉬운 설명**:

- 생성된 답변이 정답과 얼마나 비슷한지 측정
- 0.4 = 40% → 정답 단어의 40%가 생성된 답변에 포함됨
- **높을수록 좋음** (정답과 유사한 답변)

**예시**:

```text
정답: "연차휴가는 15일이며, 1년 근무 후 부여됩니다."
생성: "연차휴가는 15일입니다."

겹치는 단어: "연차휴가는", "15일"
→ ROUGE ≈ 50%
```

### 2.3 실행 시간 (exec_time)

| Vector DB | 실행 시간 | 비고 |
| --------- | --------- | ---- |
| Qdrant    | 1.29s     | 가장 빠름 |
| Weaviate  | 1.45s     | |
| Milvus    | 1.61s     | |

**쉬운 설명**:

- 전체 RAG 파이프라인 실행 시간 (검색 + 생성)
- 이 테스트에서는 Qdrant가 가장 빠름

## 3. 상세 결과 분석

### 3.1 RAG 파이프라인 구조

```text
┌─────────────────────────────────────────────────────────────┐
│                    RAG 파이프라인                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [질문] ──→ [검색] ──→ [프롬프트 생성] ──→ [답변 생성]        │
│              │              │                  │            │
│         VectorDB      ChatFstring        LlamaIndexLLM      │
│         (0.05s)       (0.00008s)           (1.45s)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 각 노드별 결과

#### 노드 1: semantic_retrieval (의미 기반 검색)

```text
module_name: VectorDB
module_params: {'top_k': 3, 'vectordb': 'weaviate_vectordb'}
execution_time: 0.049s
retrieval_f1: 0.475
retrieval_recall: 0.95
retrieval_precision: 0.317
```

**파라미터 설명**:

| 파라미터 | 값 | 의미 |
| -------- | -- | ---- |
| `top_k` | 3 | 상위 3개 문서만 검색 |
| `vectordb` | weaviate_vectordb | Weaviate DB 사용 |

**결과 해석**:

- **0.049초** 만에 검색 완료 (매우 빠름)
- **95%의 정답 문서**를 찾음 (Recall 높음)
- 하지만 검색된 문서 중 **31.7%만 실제 정답** (Precision 낮음)
- 이는 `top_k=3`으로 설정되어 정답이 아닌 문서도 포함되기 때문

#### 노드 2: prompt_maker (프롬프트 생성)

```text
module_name: ChatFstring
prompt: [
  {'role': 'system', 'content': '주어진 passage만을 이용하여 질문에 답하시오.'},
  {'role': 'user', 'content': 'passage: {retrieved_contents}\n\nQuestion: {query}\n\nAnswer:'}
]
execution_time: 0.00008s
```

**역할**:

- 검색된 문서와 질문을 LLM에게 전달할 프롬프트로 조합
- 거의 시간이 걸리지 않음 (단순 문자열 조합)

**생성되는 프롬프트 예시**:

```text
[System] 주어진 passage만을 이용하여 질문에 답하시오.

[User] passage: 제10조(연차유급휴가) ① 사용자는 1년간 80퍼센트 이상
출근한 근로자에게 15일의 유급휴가를 주어야 한다...

Question: 연차휴가는 몇 일인가요?

Answer:
```

#### 노드 3: generator (답변 생성)

```text
module_name: LlamaIndexLLM
model: openai/gpt-oss-120b
execution_time: 1.45s
average_output_token: 2848.8
rouge: 0.392
```

**파라미터 설명**:

| 파라미터 | 값 | 의미 |
| -------- | -- | ---- |
| `model` | gpt-oss-120b | 1200억 파라미터 LLM |
| `temperature` | 0.1 | 낮을수록 일관된 답변 |
| `max_tokens` | 4096 | 최대 생성 토큰 수 |

**결과 해석**:

- LLM 호출에 **1.45초** 소요 (전체 시간의 대부분)
- 평균 **2848 토큰** 생성 (꽤 긴 답변)
- ROUGE **0.392** → 정답과 약 40% 유사

## 4. 결과 해석 가이드

### 4.1 이 결과가 좋은 건가요?

| 지표 | 값 | 평가 | 설명 |
| ---- | -- | ---- | ---- |
| Recall | 0.95 | 우수 | 정답 문서 대부분을 찾음 |
| Precision | 0.317 | 보통 | 불필요한 문서도 포함됨 |
| F1 | 0.475 | 보통 | 검색 성능 개선 여지 있음 |
| ROUGE | 0.39~0.42 | 보통 | 답변 품질 개선 여지 있음 |

### 4.2 성능 개선 방법

#### 검색 성능 개선 (Precision 향상)

```yaml
# 방법 1: top_k 줄이기
top_k: 2  # 3 → 2로 줄이면 Precision 상승

# 방법 2: Reranker 추가
- node_type: passage_reranker
  modules:
    - module_type: cohere_reranker  # 검색 결과 재정렬
```

#### 생성 성능 개선 (ROUGE 향상)

```yaml
# 방법 1: 더 좋은 프롬프트
prompt:
  - role: system
    content: "당신은 인사규정 전문가입니다. 주어진 문서만을 참고하여
              정확하고 간결하게 답변하세요."

# 방법 2: 다른 LLM 모델 시도
model: openai/gpt-4  # 더 성능 좋은 모델
```

### 4.3 Vector DB 선택 가이드

이 테스트에서 세 Vector DB의 **검색 성능은 동일**합니다:

```text
Milvus = Weaviate = Qdrant (F1: 0.475, Recall: 0.95)
```

차이점:

| Vector DB | 장점 | 단점 |
| --------- | ---- | ---- |
| **Qdrant** | 가장 빠름 (1.29s), 설정 간단 | 상대적으로 새로운 프로젝트 |
| **Weaviate** | GraphQL 지원, 하이브리드 검색 | 메모리 사용량 높음 |
| **Milvus** | 대규모 확장성, 검증된 안정성 | 설정이 복잡함 |

## 5. 결과 파일 위치

```text
logs/testCase/hr_rule_weaviate/trial/0/
├── summary.csv                          # 전체 요약
├── config.yaml                          # 사용된 설정
├── retrieve_node_line/
│   └── semantic_retrieval/
│       ├── summary.csv                  # 검색 노드 결과
│       └── 0.parquet                    # 상세 데이터
└── post_retrieve_node_line/
    ├── prompt_maker/
    │   └── summary.csv                  # 프롬프트 노드 결과
    └── generator/
        ├── summary.csv                  # 생성 노드 결과
        └── 0.parquet                    # 생성된 답변 상세
```

## 6. 결과 확인 명령어

```bash
# 전체 요약 보기
cat logs/testCase/hr_rule_weaviate/trial/0/summary.csv

# 검색 성능 상세
cat logs/testCase/hr_rule_weaviate/trial/0/retrieve_node_line/semantic_retrieval/summary.csv

# 생성 성능 상세
cat logs/testCase/hr_rule_weaviate/trial/0/post_retrieve_node_line/generator/summary.csv

# 여러 테스트 결과 비교
make compare-results

# 웹 대시보드로 보기
make dashboard TRIAL_DIR=logs/testCase/hr_rule_weaviate/trial/0
```

## 7. 용어 정리

| 용어 | 영어 | 설명 |
| ---- | ---- | ---- |
| 검색 | Retrieval | 질문과 관련된 문서를 찾는 것 |
| 재현율 | Recall | 정답 중 찾은 비율 |
| 정밀도 | Precision | 검색 결과 중 정답 비율 |
| F1 | F1 Score | Recall과 Precision의 조화 평균 |
| ROUGE | ROUGE | 생성된 텍스트와 정답의 유사도 |
| top_k | Top-K | 상위 K개 결과만 반환 |
| 토큰 | Token | LLM이 처리하는 텍스트 단위 (약 0.75 단어) |
