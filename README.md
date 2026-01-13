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

## 빠른 시작

```bash
# 환경변수 설정
export OPENAI_API_KEY="your-api-key"

# 샘플 데이터로 빠른 테스트
make quick-test

# 커스텀 LLM 서버 사용 시 (OpenAI API 키 불필요)
make quick-test-custom

# 결과 대시보드
make dashboard
```

자세한 내용은 [빠른 테스트 가이드](docs/note-roy/빠른테스트.md) 참조.

---

## Make 명령어

```bash
make              # 도움말 표시
```

| 명령어 | 설명 |
|--------|------|
| `make install` | 기본 설치 |
| `make install-dev` | 개발 환경 설치 (uv) |
| `make setup-nltk` | NLTK 데이터 설치 |
| `make lint` | ruff 린터 실행 |
| `make format` | ruff 포맷터 실행 |
| `make test` | 전체 테스트 실행 |
| `make quick-test` | 샘플 데이터로 RAG 평가 |
| `make quick-test-custom` | 커스텀 LLM 서버로 평가 |
| `make dashboard` | 결과 대시보드 (7690) |
| `make api` | API 서버 (8000) |
| `make web` | 웹 인터페이스 |
| `make clean` | 결과/캐시 삭제 |

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
