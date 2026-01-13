# 샘플 데이터셋 사용 가이드

sample_dataset 폴더에는 `qa.parquet`, `corpus.parquet` 파일이 포함되어 있지 않습니다. 이 파일들은 용량이 크기 때문에 Git에 직접 업로드할 수 없습니다.

sample_dataset 폴더에서 제공하는 데이터셋(`triviaqa`, `hotpotqa`, `msmarco`, `eli5`)을 사용하려면 아래 방법을 따르세요.

## 사용 방법

아래 예시는 `triviaqa`를 사용하지만, `msmarco`, `eli5`, `hotpotqa`도 동일한 방식으로 사용할 수 있습니다.

### 1. 저장 경로를 지정하여 실행

터미널에서 Python 스크립트를 실행하고 데이터셋을 특정 경로에 저장하려면 다음 명령을 사용하세요:

```bash
python ./sample_dataset/triviaqa/load_triviaqa_dataset.py --save_path /path/to/save/dataset
```

이 명령은 `./sample_dataset/triviaqa/` 디렉토리에 있는 `load_triviaqa_dataset.py` 스크립트를 실행하며, `--save_path` 인자로 데이터셋 저장 위치를 지정합니다.

### 2. 저장 경로 없이 실행

`--save_path` 인자 없이 스크립트를 실행하면, 데이터셋은 기본 위치인 `load_triviaqa_dataset.py` 파일이 있는 디렉토리(`./sample_dataset/triviaqa/`)에 저장됩니다:

```bash
python ./sample_dataset/triviaqa/load_triviaqa_dataset.py
```

이 방식은 경로를 지정할 필요 없이 간단하게 실행할 수 있어, 빠른 테스트나 대상 디렉토리에서 직접 작업할 때 편리합니다.
