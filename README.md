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

---

## 빠른 시작

### 1. RAG 파이프라인 평가

```bash
autorag evaluate --config config.yaml --qa_data_path qa.parquet --corpus_data_path corpus.parquet
```

### 2. 결과 대시보드

```bash
autorag dashboard --trial_dir ./0
```

### 3. 최적 파이프라인 배포

```bash
# API 서버
autorag run_api --trial_dir ./0 --host 0.0.0.0 --port 8000

# 웹 인터페이스
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
