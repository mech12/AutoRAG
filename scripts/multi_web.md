# AutoRAG 멀티 테스트 케이스 웹 인터페이스

`multi_web.py` (localhost:8501)의 UI 요소 설명

## 사이드바 (Sidebar)
- **테스트 케이스 선택** (`st.selectbox`) - 드롭다운으로 테스트 케이스 선택
- **테스트 케이스 정보** - 설명, 청크 크기, QA 개수 표시

## 메인 영역
- **제목**: "🤖 AutoRAG 멀티 테스트 케이스"
- **설명 텍스트**: "테스트 케이스를 선택하고 질문을 입력하세요."
- **채팅 히스토리** (`st.chat_message`) - 대화 내역 표시
- **질문 입력창** (`st.chat_input`) - "질문을 입력하세요..."
- **RAG 응답** - 답변 + 참조 문서 (최대 3개)

## 상태 표시
- `st.spinner`: "RAG 파이프라인 로딩 중...", "답변 생성 중..."
- `st.success`: "파이프라인 로드 완료!"
- `st.error`: 오류 메시지
- `st.warning`: 테스트 케이스 없을 때 안내

## 사용법

```bash
# Streamlit 직접 실행
streamlit run scripts/multi_web.py

# Makefile 사용
make multi-web
```
