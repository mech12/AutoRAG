# AutoRAG

데이터에 최적화된 RAG 파이프라인을 자동으로 찾아주는 RAG AutoML 도구입니다.

![Thumbnail](https://github.com/user-attachments/assets/6bab243d-a4b3-431a-8ac0-fe17336ab4de)

![PyPI - Downloads](https://img.shields.io/pypi/dm/AutoRAG)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/company/104375108/admin/dashboard/)
![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/AutoRAG_HQ)

📖 [문서](https://marker-inc-korea.github.io/AutoRAG/) | 📋 [전체 README](README-org.md)

---

## 설치

Python 3.10 이상 권장

```bash
source .venv/bin/activate

# 기본 설치
pip install AutoRAG

# GPU 버전 (로컬 모델 사용 시)
pip install "AutoRAG[gpu]"

# 파싱 기능 포함
pip install "AutoRAG[gpu,parse]"
```

### 개발 환경 설치

```bash
# uv 사용 (권장)
uv venv && source .venv/bin/activate
uv sync --all-extras

# 필수 후속 설치
pip install --upgrade pyOpenSSL nltk
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"
```

### 자동 가상환경 활성화 (direnv)

프로젝트 폴더 진입 시 자동으로 가상환경 활성화:

```bash
# 1. direnv 설치
brew install direnv

# 2. 쉘 설정 추가 (zsh)
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# 3. 프로젝트에 .envrc 생성
echo 'source .venv/bin/activate' > .envrc
direnv allow
```

---

## 전체 흐름

```
원시 문서 (PDF 등) → 파싱 → 청킹 → QA 생성 → RAG 최적화
                      ↓        ↓         ↓
              parsed.parquet  corpus.parquet  qa.parquet
```

---

## 빠른 테스트 (샘플 데이터)

```bash
# 환경변수 설정
export OPENAI_API_KEY="your-api-key"

# 샘플 데이터로 RAG 최적화 실행
autorag evaluate \
  --config sample_config/rag/korean/non_gpu/simple_korean.yaml \
  --qa_data_path tests/resources/dataset_sample_gen_by_autorag/qa.parquet \
  --corpus_data_path tests/resources/dataset_sample_gen_by_autorag/corpus.parquet

# 결과 대시보드
autorag dashboard --trial_dir ./0
```

---

## 데이터 생성

### 1. 파싱 설정 (parse_config.yaml)

```yaml
modules:
  - module_type: langchain_parse
    parse_method: pdfminer
```

### 2. 청킹 설정 (chunk_config.yaml)

```yaml
modules:
  - module_type: llama_index_chunk
    chunk_method: Token
    chunk_size: 1024
    chunk_overlap: 24
    add_file_name: ko
```

### 3. 데이터 생성 스크립트

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"

import pandas as pd
from llama_index.llms.openai import OpenAI
from autorag.parser import Parser
from autorag.chunker import Chunker
from autorag.data.qa.filter.dontknow import dontknow_filter_rule_based
from autorag.data.qa.generation_gt.llama_index_gen_gt import make_basic_gen_gt, make_concise_gen_gt
from autorag.data.qa.schema import Raw, Corpus
from autorag.data.qa.query.llama_gen_query import factoid_query_gen
from autorag.data.qa.sample import random_single_hop

# 1. 파싱
parser = Parser(data_path_glob="data/*")
parser.start_parsing("parse_config.yaml")

# 2. 청킹
chunker = Chunker.from_parquet(parsed_data_path="0/parsed.parquet")
chunker.start_chunking("chunk_config.yaml")

# 3. QA 생성
llm = OpenAI(model="gpt-4o-mini")
raw_df = pd.read_parquet("0/parsed.parquet")
raw_instance = Raw(raw_df)

corpus_df = pd.read_parquet("0/0/corpus.parquet")
corpus_instance = Corpus(corpus_df, raw_instance)

initial_qa = (
    corpus_instance.sample(random_single_hop, n=10)
    .map(lambda df: df.reset_index(drop=True))
    .make_retrieval_gt_contents()
    .batch_apply(factoid_query_gen, llm=llm)
    .batch_apply(make_basic_gen_gt, llm=llm)
    .batch_apply(make_concise_gen_gt, llm=llm)
    .filter(dontknow_filter_rule_based, lang="ko")
)

initial_qa.to_parquet('./qa.parquet', './corpus.parquet')
```

---

## RAG 최적화 실행

```bash
# 환경변수 설정
export OPENAI_API_KEY="your-api-key"

# RAG 최적화 실행
autorag evaluate \
  --config sample_config/rag/korean/non_gpu/simple_korean.yaml \
  --qa_data_path qa.parquet \
  --corpus_data_path corpus.parquet

# 결과 대시보드
autorag dashboard --trial_dir ./0

# API 서버 실행
autorag run_api --trial_dir ./0 --host 0.0.0.0 --port 8000

# 웹 인터페이스 실행
autorag run_web --trial_path ./0
```

---

## CLI 명령어

| 명령어 | 설명 |
|--------|------|
| `autorag evaluate` | RAG 파이프라인 평가 실행 |
| `autorag validate` | 설정 파일 유효성 검사 |
| `autorag dashboard` | 결과 대시보드 실행 |
| `autorag run_api` | API 서버 실행 |
| `autorag run_web` | 웹 인터페이스 실행 |

---

## 참고 자료

- [빠른 테스트 가이드](docs/note-roy/빠른테스트.md)
- [청킹(Chunking) 가이드](docs/note-roy/청킹에%20대해.md)
- [샘플 설정 파일](sample_config/rag)
- [지원 모듈 목록](https://edai.notion.site/Supporting-Nodes-modules-0ebc7810649f4e41aead472a92976be4)
- [문제 해결](https://medium.com/@autorag/autorag-troubleshooting-5cf872b100e3)

## 인용

```bibtex
@misc{kim2024autoragautomatedframeworkoptimization,
      title={AutoRAG: Automated Framework for optimization of Retrieval Augmented Generation Pipeline},
      author={Dongkyu Kim and Byoungwook Kim and Donggeon Han and Matouš Eibich},
      year={2024},
      eprint={2410.20878},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2410.20878},
}
```
