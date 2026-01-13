# AutoRAG

데이터에 최적화된 RAG 파이프라인을 자동으로 찾아주는 RAG AutoML 도구입니다.

![Thumbnail](https://github.com/user-attachments/assets/6bab243d-a4b3-431a-8ac0-fe17336ab4de)

![PyPI - Downloads](https://img.shields.io/pypi/dm/AutoRAG)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/company/104375108/admin/dashboard/)
![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/AutoRAG_HQ)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Follow-orange?style=flat-square&logo=huggingface)](https://huggingface.co/AutoRAG)

<a href="https://trendshift.io/repositories/7832" target="_blank"><img src="https://trendshift.io/api/badge/repositories/7832" alt="Marker-Inc-Korea%2FAutoRAG | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

다양한 RAG 파이프라인과 모듈이 존재하지만,
"여러분의 데이터"와 "여러분의 사용 사례"에 어떤 파이프라인이 적합한지 알 수 없습니다.
모든 RAG 모듈을 직접 만들고 평가하는 것은 매우 시간이 많이 걸리고 어렵습니다.
하지만 이 과정 없이는 여러분의 사용 사례에 가장 적합한 RAG 파이프라인을 결코 알 수 없습니다.

AutoRAG는 "여러분의 데이터"에 최적화된 RAG 파이프라인을 찾아주는 도구입니다.
여러분만의 평가 데이터로 다양한 RAG 모듈을 자동으로 평가하고
여러분의 사용 사례에 가장 적합한 RAG 파이프라인을 찾을 수 있습니다.

AutoRAG는 다양한 RAG 모듈 조합을 간단하게 평가할 수 있는 방법을 제공합니다.
지금 바로 시도해보고 여러분의 사용 사례에 가장 적합한 RAG 파이프라인을 찾아보세요.

📖 [문서](https://marker-inc-korea.github.io/AutoRAG/)를 살펴보세요!!

---

## YouTube 튜토리얼

https://github.com/Marker-Inc-Korea/AutoRAG/assets/96727832/c0d23896-40c0-479f-a17b-aa2ec3183a26

_기본적으로 음소거 상태입니다. 음성 해설을 들으려면 사운드를 켜세요_

[YouTube](https://youtu.be/2ojK8xjyXAU?feature=shared)에서도 볼 수 있습니다

## HuggingFace Space에서 AutoRAG 사용하기 🚀

- [💬 Naive RAG 챗봇](https://huggingface.co/spaces/AutoRAG/Naive-RAG-chatbot)
- [✏️ AutoRAG 데이터 생성](https://huggingface.co/spaces/AutoRAG/AutoRAG-data-creation)
- [🚀 AutoRAG RAG 파이프라인 최적화](https://huggingface.co/spaces/AutoRAG/RAG-Pipeline-Optimization)

## Colab 튜토리얼

- [1단계: AutoRAG 기초 | RAG 파이프라인 최적화하기](https://colab.research.google.com/drive/19OEQXO_pHN6gnn2WdfPd4hjnS-4GurVd?usp=sharing)
- [2단계: 데이터 생성 | RAG 최적화를 위한 나만의 데이터 만들기](https://colab.research.google.com/drive/1BOdzMndYgMY_iqhwKcCCS7ezHbZ4Oz5X?usp=sharing)
- [3단계: 커스텀 LLM 및 임베딩 모델 사용 | 커스텀 모델 사용하기](https://colab.research.google.com/drive/12VpWcSTSOsLSyW0BKb-kPoEzK22ACxvS?usp=sharing)

# 목차

- [빠른 설치](#빠른-설치)
- [데이터 생성](#데이터-생성)
    - [파싱](#1-파싱)
    - [청킹](#2-청킹)
    - [QA 생성](#3-qa-생성)
- [RAG 최적화](#rag-최적화)
    - [AutoRAG는 RAG 파이프라인을 어떻게 최적화하나요?](#autorag는-rag-파이프라인을-어떻게-최적화하나요)
    - [메트릭](#메트릭)
    - [빠른 시작](#빠른-시작-1)
        - [YAML 파일 설정](#1-yaml-파일-설정)
        - [AutoRAG 실행](#2-autorag-실행)
        - [대시보드 실행](#3-대시보드-실행)
        - [최적의 RAG 파이프라인 배포](#4-최적의-rag-파이프라인-배포)
- [자주 묻는 질문](#-자주-묻는-질문)

# 빠른 설치

AutoRAG는 Python 버전 3.10 이상을 권장합니다.

```bash
pip install AutoRAG
```

로컬 모델을 사용하려면 GPU 버전을 설치해야 합니다.

```bash
pip install "AutoRAG[gpu]"
```

또는 파싱 기능을 위해 파싱 버전을 사용할 수 있습니다.

```bash
pip install "AutoRAG[gpu,parse]"
```

# 데이터 생성

<a href="https://huggingface.co/spaces/AutoRAG/AutoRAG-data-creation">
<img src="https://github.com/user-attachments/assets/8c6e4b02-3938-4560-b817-c95764965b50" alt="Hugging Face Sticker" style="width:200px;height:auto;">
</a>

![Image](https://github.com/user-attachments/assets/146d005d-dcb9-4460-a8b3-25126e5e3dc2)

![image](https://github.com/user-attachments/assets/6079f696-207c-4221-8d28-5561a203dfe2)

RAG 최적화에는 두 가지 유형의 데이터가 필요합니다: QA 데이터셋과 코퍼스 데이터셋.

1. **QA** 데이터셋 파일 (qa.parquet)
2. **코퍼스** 데이터셋 파일 (corpus.parquet)

**QA** 데이터셋은 정확하고 신뢰할 수 있는 평가 및 최적화에 중요합니다.

**코퍼스** 데이터셋은 RAG의 성능에 매우 중요합니다.
RAG는 코퍼스를 사용하여 문서를 검색하고 이를 기반으로 답변을 생성하기 때문입니다.

### 📌 지원하는 데이터 생성 모듈

![Image](https://github.com/user-attachments/assets/c6f15fab-6c69-4627-9685-6c218b66f5d6)

- [지원하는 파싱 모듈 목록](https://edai.notion.site/Supporting-Parsing-Modules-e0b7579c7c0e4fb2963e408eeccddd75?pvs=4)
- [지원하는 청킹 모듈 목록](https://edai.notion.site/Supporting-Chunk-Modules-8db803dba2ec4cd0a8789659106e86a3?pvs=4)

## 빠른 시작

### 1. 파싱

#### YAML 파일 설정

```yaml
modules:
  - module_type: langchain_parse
    parse_method: pdfminer
```

여러 개의 파싱 모듈을 동시에 사용할 수도 있습니다.
하지만 이 경우 각 파싱 결과에 대해 새로운 프로세스를 반환해야 합니다.

#### 파싱 시작

몇 줄의 코드만으로 원시 문서를 파싱할 수 있습니다.

```python
from autorag.parser import Parser

parser = Parser(data_path_glob="your/data/path/*")
parser.start_parsing("your/path/to/parse_config.yaml")
```

### 2. 청킹

#### YAML 파일 설정

```yaml
modules:
  - module_type: llama_index_chunk
    chunk_method: Token
    chunk_size: 1024
    chunk_overlap: 24
    add_file_name: en
```

여러 개의 청크 모듈을 동시에 사용할 수도 있습니다.
이 경우 하나의 코퍼스를 사용하여 QA를 생성한 다음 나머지 코퍼스를 QA 데이터에 매핑해야 합니다.
청크 방법이 다르면 retrieval_gt가 달라지므로 QA 데이터셋에 다시 매핑해야 합니다.

#### 청킹 시작

몇 줄의 코드만으로 파싱된 결과를 청킹할 수 있습니다.

```python
from autorag.chunker import Chunker

chunker = Chunker.from_parquet(parsed_data_path="your/parsed/data/path")
chunker.start_chunking("your/path/to/chunk_config.yaml")
```

### 3. QA 생성

몇 줄의 코드만으로 QA 데이터셋을 생성할 수 있습니다.

```python
import pandas as pd
from llama_index.llms.openai import OpenAI

from autorag.data.qa.filter.dontknow import dontknow_filter_rule_based
from autorag.data.qa.generation_gt.llama_index_gen_gt import (
	make_basic_gen_gt,
	make_concise_gen_gt,
)
from autorag.data.qa.schema import Raw, Corpus
from autorag.data.qa.query.llama_gen_query import factoid_query_gen
from autorag.data.qa.sample import random_single_hop

llm = OpenAI()
raw_df = pd.read_parquet("your/path/to/parsed.parquet")
raw_instance = Raw(raw_df)

corpus_df = pd.read_parquet("your/path/to/corpus.parquet")
corpus_instance = Corpus(corpus_df, raw_instance)

initial_qa = (
	corpus_instance.sample(random_single_hop, n=3)
	.map(
		lambda df: df.reset_index(drop=True),
	)
	.make_retrieval_gt_contents()
	.batch_apply(
		factoid_query_gen,  # 쿼리 생성
		llm=llm,
	)
	.batch_apply(
		make_basic_gen_gt,  # 답변 생성 (기본)
		llm=llm,
	)
	.batch_apply(
		make_concise_gen_gt,  # 답변 생성 (간결)
		llm=llm,
	)
	.filter(
		dontknow_filter_rule_based,  # "모르겠습니다" 필터링
		lang="en",
	)
)

initial_qa.to_parquet('./qa.parquet', './corpus.parquet')
```

# RAG 최적화

<a href="https://huggingface.co/spaces/AutoRAG/RAG-Pipeline-Optimization">
<img src="https://github.com/user-attachments/assets/8c6e4b02-3938-4560-b817-c95764965b50" alt="Hugging Face Sticker" style="width:200px;height:auto;">
</a>

![Image](https://github.com/user-attachments/assets/b814928d-54a4-4b96-af34-adba0ac6803b)

![rag](https://github.com/user-attachments/assets/214d842e-fc67-4113-9c24-c94158b00c23)

## AutoRAG는 RAG 파이프라인을 어떻게 최적화하나요?

다음은 노드만 표시한 AutoRAG RAG 구조입니다.

![Image](https://github.com/user-attachments/assets/cbc60938-e211-4fbf-be74-31bd9a997581)

다음은 모든 노드와 모듈을 보여주는 이미지입니다.

![Image](https://github.com/user-attachments/assets/9489e803-f47a-49d4-97ec-0dd9b270394f)

![rag_opt_gif](https://github.com/user-attachments/assets/55bd09cd-8420-4f6d-bc7d-0a66af288317)

### 📌 지원하는 RAG 최적화 노드 및 모듈

- [지원하는 RAG 모듈 목록](https://edai.notion.site/Supporting-Nodes-modules-0ebc7810649f4e41aead472a92976be4?pvs=4)

## 메트릭

AutoRAG에서 각 노드가 사용하는 메트릭은 아래와 같습니다.

![Image](https://github.com/user-attachments/assets/5b342f68-d25c-4cba-aa85-1e257801afea)

![Image](https://github.com/user-attachments/assets/393d3ad6-1bde-4e75-b314-5c150eadaeee)

- [지원하는 메트릭 목록](https://edai.notion.site/Supporting-metrics-867d71caefd7401c9264dd91ba406043?pvs=4)

AutoRAG가 지원하는 메트릭에 대한 자세한 정보는 다음과 같습니다.

- [검색 메트릭](https://edai.notion.site/Retrieval-Metrics-dde3d9fa1d9547cdb8b31b94060d21e7?pvs=4)
- [검색 토큰 메트릭](https://edai.notion.site/Retrieval-Token-Metrics-c3e2d83358e04510a34b80429ebb543f?pvs=4)
- [생성 메트릭](https://github.com/user-attachments/assets/7d4a3069-9186-4854-885d-ca0f7bcc17e8)

## 빠른 시작

### 1. YAML 파일 설정

먼저 RAG 최적화를 위한 설정 YAML 파일을 설정해야 합니다.

초보자에게는 미리 만들어진 설정 YAML 파일을 사용하는 것을 강력히 권장합니다.

- [샘플 YAML 가져오기](sample_config/rag)
    - [샘플 YAML 가이드](https://marker-inc-korea.github.io/AutoRAG/optimization/sample_config.html)
- [커스텀 YAML 만들기 가이드](https://marker-inc-korea.github.io/AutoRAG/optimization/custom_config.html)

다음은 3개의 검색 노드, `prompt_maker`, `generator` 노드를 사용하는 설정 YAML 파일의 예시입니다.

```yaml
node_lines:
  - node_line_name: retrieve_node_line
    nodes:
      - node_type: lexical_retrieval
        strategy:
          metrics: [ retrieval_f1, retrieval_recall, retrieval_ndcg, retrieval_mrr ]
        top_k: 3
        modules:
          - module_type: bm25
      - node_type: semantic_retrieval
        strategy:
          metrics: [ retrieval_f1, retrieval_recall, retrieval_ndcg, retrieval_mrr ]
        top_k: 3
        modules:
          - module_type: vectordb
            vectordb: default
      - node_type: hybrid_retrieval
        strategy:
          metrics: [ retrieval_f1, retrieval_recall, retrieval_ndcg, retrieval_mrr ]
        top_k: 3
        modules:
          - module_type: hybrid_rrf
            weight_range: (4,80)
  - node_line_name: post_retrieve_node_line
    nodes:
      - node_type: prompt_maker  # 프롬프트 메이커 노드 설정
        strategy:
          metrics: # 생성 메트릭 설정
            - metric_name: meteor
            - metric_name: rouge
            - metric_name: sem_score
              embedding_model: openai
        modules:
          - module_type: fstring
            prompt: "Read the passages and answer the given question. \n Question: {query} \n Passage: {retrieved_contents} \n Answer : "
      - node_type: generator  # 생성기 노드 설정
        strategy:
          metrics: # 생성 메트릭 설정
            - metric_name: meteor
            - metric_name: rouge
            - metric_name: sem_score
              embedding_model: openai
        modules:
          - module_type: openai_llm
            llm: gpt-4o-mini
            batch: 16
```

### 2. AutoRAG 실행

몇 줄의 코드만으로 RAG 파이프라인을 평가할 수 있습니다.

```python
from autorag.evaluator import Evaluator

evaluator = Evaluator(qa_data_path='your/path/to/qa.parquet', corpus_data_path='your/path/to/corpus.parquet')
evaluator.start_trial('your/path/to/config.yaml')
```

또는 명령줄 인터페이스를 사용할 수 있습니다

```bash
autorag evaluate --config your/path/to/default_config.yaml --qa_data_path your/path/to/qa.parquet --corpus_data_path your/path/to/corpus.parquet
```

완료되면 현재 디렉토리에 여러 파일과 폴더가 생성된 것을 볼 수 있습니다.
숫자로 이름이 지정된 trial 폴더(예: 0)에서
평가 결과와 데이터에 가장 적합한 RAG 파이프라인을 요약한 `summary.csv` 파일을 확인할 수 있습니다.

더 자세한 내용은 [여기](https://marker-inc-korea.github.io/AutoRAG/optimization/folder_structure.html)에서 폴더 구조가 어떻게 생겼는지 확인할 수 있습니다.

### 3. 대시보드 실행

대시보드를 실행하여 결과를 쉽게 볼 수 있습니다.

```bash
autorag dashboard --trial_dir /your/path/to/trial_dir
```

#### 샘플 대시보드

![dashboard](https://github.com/Marker-Inc-Korea/AutoRAG/assets/96727832/3798827d-31d7-4c4e-a9b1-54340b964e53)

### 4. 최적의 RAG 파이프라인 배포

### 4-1. 코드로 실행

trial 폴더에서 바로 최적의 RAG 파이프라인을 사용할 수 있습니다.
trial 폴더는 대시보드 실행에 사용된 디렉토리입니다. (예: 0, 1, 2, ...)

```python
from autorag.deploy import Runner

runner = Runner.from_trial_folder('/your/path/to/trial_dir')
runner.run('your question')
```

### 4-2. API 서버로 실행

이 파이프라인을 API 서버로 실행할 수 있습니다.

API 엔드포인트는 [여기](./docs/source/deploy/api_endpoint.md)에서 확인하세요.

```python
import nest_asyncio
from autorag.deploy import ApiRunner

nest_asyncio.apply()

runner = ApiRunner.from_trial_folder('/your/path/to/trial_dir')
runner.run_api_server()
```

```bash
autorag run_api --trial_dir your/path/to/trial_dir --host 0.0.0.0 --port 8000
```

CLI 명령은 추출된 설정 YAML 파일을 사용합니다. 더 자세히 알고 싶으시면
[여기](https://marker-inc-korea.github.io/AutoRAG/tutorial.html#extract-pipeline-and-evaluate-test-dataset)를 확인하세요.

### 4-3. 웹 인터페이스로 실행

이 파이프라인을 웹 인터페이스로 실행할 수 있습니다.

웹 인터페이스는 [여기](deploy/web.md)에서 확인하세요.

```bash
autorag run_web --trial_path your/path/to/trial_path
```

#### 샘플 웹 인터페이스

<img width="1491" alt="web_interface" src="https://github.com/Marker-Inc-Korea/AutoRAG/assets/96727832/f6b00353-f6bb-4d8f-8740-1c264c0acbb8">

## ☎️ 자주 묻는 질문

💻 [하드웨어 사양](https://edai.notion.site/Hardware-specs-28cefcf2a26246ffadc91e2f3dc3d61c?pvs=4)

⭐ [AutoRAG 실행하기](https://edai.notion.site/About-running-AutoRAG-44a8058307af42068fc218a073ee480b?pvs=4)

🍯 [팁/트릭](https://edai.notion.site/Tips-Tricks-10708a0e36ff461cb8a5d4fb3279ff15?pvs=4)

☎️ [문제 해결](https://medium.com/@autorag/autorag-troubleshooting-5cf872b100e3)

## 추천해주셔서 감사합니다

### 기업

<a href="https://www.linkedin.com/posts/llamaindex_rag-pipelines-have-a-lot-of-hyperparameters-activity-7182053546593247232-HFMN/">
<img src="https://github.com/user-attachments/assets/b8fdaaf6-543a-4019-8dbe-44191a5269b9" alt="llama index" style="width:200px;height:auto;">
</a>

### 개인

- [Shubham Saboo](https://www.linkedin.com/posts/shubhamsaboo_just-found-the-solution-to-the-biggest-rag-activity-7255404464054939648-ISQ8/)
- [Kalyan KS](https://www.linkedin.com/posts/kalyanksnlp_rag-autorag-llms-activity-7258677155574788097-NgS0/)

---

# ✨ 기여자 ✨

멋진 분들께 감사드립니다:

<a href="https://github.com/Marker-Inc-Korea/AutoRAG/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Marker-Inc-Korea/AutoRAG" />
</a>

# 기여

저희는 AutoRAG를 오픈소스로 개발하고 있습니다.

따라서 이 프로젝트는 기여와 제안을 환영합니다. 이 프로젝트에 자유롭게 기여해주세요.

또한 [여기](https://marker-inc-korea.github.io/AutoRAG/index.html)에서 자세한 문서를 확인하세요.

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
