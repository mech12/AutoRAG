#!/usr/bin/env python3
"""
AutoRAG 통합 비교 웹 인터페이스

두 탭으로 구성:
1. Compare Dashboard: 두 테스트 케이스의 평가 결과 비교
2. QA Test: 두 테스트 케이스에 동일한 질문 비교

사용법:
    streamlit run scripts/compare_web.py --server.port 8502

    또는 Makefile:
    make compare-web
"""

import ast
import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import streamlit as st
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from testcase_config import list_testcases, load_testcase

# ============================================================================
# 용어 사전 (Glossary)
# ============================================================================

GLOSSARY = {
    "retrieval_recall": {
        "term": "재현율 (Recall)",
        "short": "정답 문서 중 찾은 비율",
        "detail": """**재현율 (Recall)** = 실제로 찾은 정답 문서 수 / 전체 정답 문서 수

**쉬운 설명**: "정답 문서 10개 중에서 몇 개를 찾았나?"
- 0.95 = 95% → 정답 문서 10개 중 9.5개를 찾음
- **높을수록 좋음** (놓치는 정답이 적음)

**예시**:
```
질문: "연차휴가는 몇 일인가요?"
정답 문서: [문서A, 문서B] (2개)
검색 결과: [문서A, 문서B, 문서C] (3개)
→ 정답 2개 중 2개를 찾음 = Recall 100%
```""",
    },
    "retrieval_precision": {
        "term": "정밀도 (Precision)",
        "short": "검색 결과 중 정답 비율",
        "detail": """**정밀도 (Precision)** = 실제로 찾은 정답 문서 수 / 검색된 전체 문서 수

**쉬운 설명**: "검색된 문서 중에서 실제 정답은 몇 개인가?"
- 0.317 = 31.7% → 검색된 3개 문서 중 약 1개만 정답
- **높을수록 좋음** (쓸데없는 문서가 적음)

**예시**:
```
질문: "연차휴가는 몇 일인가요?"
검색 결과: [문서A, 문서B, 문서C] (3개)
이 중 정답: [문서A] (1개)
→ 검색 3개 중 정답 1개 = Precision 33%
```""",
    },
    "retrieval_f1": {
        "term": "F1 점수",
        "short": "Recall과 Precision의 조화 평균",
        "detail": """**F1 점수** = 2 × Precision × Recall / (Precision + Recall)

**쉬운 설명**: Recall과 Precision의 **조화 평균**으로, 두 지표를 균형있게 평가합니다.

**왜 F1을 사용하나?**
```
Case 1: Recall 100%, Precision 10%
  → 모든 문서를 다 가져오면 정답은 다 찾지만 쓸데없는 것도 많음

Case 2: Recall 10%, Precision 100%
  → 확실한 것만 가져오면 정확하지만 놓치는 정답이 많음

F1은 이 둘의 균형을 측정
```""",
    },
    "rouge": {
        "term": "ROUGE",
        "short": "생성된 텍스트와 정답의 유사도",
        "detail": """**ROUGE (Recall-Oriented Understudy for Gisting Evaluation)**

ROUGE 점수 = 생성된 답변과 정답이 겹치는 단어 수 / 정답의 전체 단어 수

**쉬운 설명**:
- 생성된 답변이 정답과 얼마나 비슷한지 측정
- 0.4 = 40% → 정답 단어의 40%가 생성된 답변에 포함됨
- **높을수록 좋음** (정답과 유사한 답변)

**예시**:
```
정답: "연차휴가는 15일이며, 1년 근무 후 부여됩니다."
생성: "연차휴가는 15일입니다."

겹치는 단어: "연차휴가는", "15일"
→ ROUGE ≈ 50%
```""",
    },
    "execution_time": {
        "term": "실행 시간",
        "short": "전체 RAG 파이프라인 실행 시간",
        "detail": """**실행 시간 (Execution Time)**

전체 RAG 파이프라인 실행 시간 = 검색 시간 + 생성 시간

**구성 요소**:
- **검색 (VectorDB)**: 약 0.05초 (매우 빠름)
- **프롬프트 생성**: 약 0.0001초 (무시 가능)
- **LLM 답변 생성**: 약 1.4초 (대부분의 시간 소요)

**Vector DB별 비교**:
| Vector DB | 실행 시간 |
|-----------|----------|
| Qdrant    | 1.29s (가장 빠름) |
| Chroma    | 1.43s |
| Weaviate  | 1.45s |
| Milvus    | 1.61s |""",
    },
    "top_k": {
        "term": "Top-K",
        "short": "상위 K개 결과만 반환",
        "detail": """**Top-K**

검색 시 상위 K개의 가장 관련성 높은 문서만 반환하는 설정입니다.

**예시**: top_k=3이면 가장 유사한 문서 3개만 반환

**영향**:
- K가 클수록 → Recall 증가, Precision 감소
- K가 작을수록 → Recall 감소, Precision 증가

**권장값**: 보통 3~10 사이""",
    },
    "semantic_retrieval": {
        "term": "의미 기반 검색",
        "short": "벡터 유사도로 문서 검색",
        "detail": """**의미 기반 검색 (Semantic Retrieval)**

문서와 질문을 벡터(숫자 배열)로 변환 후, 벡터 유사도를 계산하여 관련 문서를 찾는 방식입니다.

**장점**:
- 키워드가 정확히 일치하지 않아도 의미적으로 유사한 문서 검색 가능
- "연차휴가"로 검색해도 "연차유급휴가" 문서를 찾을 수 있음

**사용되는 Vector DB**: Milvus, Weaviate, Qdrant, Chroma 등""",
    },
    "generator": {
        "term": "생성기 (Generator)",
        "short": "LLM으로 답변 생성",
        "detail": """**생성기 (Generator)**

검색된 문서(Context)를 바탕으로 LLM이 최종 답변을 생성하는 단계입니다.

**파라미터**:
- `model`: 사용할 LLM 모델 (예: gpt-4, gpt-oss-120b)
- `temperature`: 낮을수록 일관된 답변 (0.1 권장)
- `max_tokens`: 최대 생성 토큰 수

**실행 시간의 대부분**이 이 단계에서 소요됩니다.""",
    },
    "prompt_maker": {
        "term": "프롬프트 생성기",
        "short": "검색 결과를 LLM 입력으로 변환",
        "detail": """**프롬프트 생성기 (Prompt Maker)**

검색된 문서와 사용자 질문을 LLM에게 전달할 프롬프트 형식으로 조합합니다.

**예시 프롬프트**:
```
[System] 주어진 passage만을 이용하여 질문에 답하시오.

[User] passage: 제10조(연차유급휴가) ① 사용자는 1년간 80퍼센트 이상
출근한 근로자에게 15일의 유급휴가를 주어야 한다...

Question: 연차휴가는 몇 일인가요?

Answer:
```""",
    },
    "VectorDB": {
        "term": "벡터 데이터베이스",
        "short": "벡터 임베딩 저장 및 유사도 검색용 DB",
        "detail": """**벡터 데이터베이스 (Vector Database)**

텍스트를 벡터(고차원 숫자 배열)로 변환하여 저장하고, 벡터 간 유사도를 빠르게 검색할 수 있는 특수 데이터베이스입니다.

**주요 Vector DB 비교**:
| Vector DB | 장점 | 단점 |
|-----------|------|------|
| **Qdrant** | 가장 빠름, 설정 간단 | 상대적으로 새로운 프로젝트 |
| **Weaviate** | GraphQL 지원, 하이브리드 검색 | 메모리 사용량 높음 |
| **Milvus** | 대규모 확장성, 검증된 안정성 | 설정이 복잡함 |
| **Chroma** | 설치 간단, 로컬 개발 적합 | 대규모에 부적합 |""",
    },
}


# ============================================================================
# 공통 유틸리티
# ============================================================================


def find_available_testcases() -> list[tuple[str, str]]:
    """실행된 테스트 케이스 목록 반환 (trial 결과가 있는 것만)"""
    available = []
    for name, desc in list_testcases():
        tc = load_testcase(name)
        trial_summary = f"{tc.trial_dir}/0/summary.csv"
        if os.path.exists(trial_summary):
            available.append((name, desc))
    return available


def get_runner(trial_path: str):
    """Runner 인스턴스 생성"""
    from autorag.deploy import Runner

    return Runner.from_trial_folder(trial_path)


def set_page_config():
    """페이지 설정"""
    st.set_page_config(
        page_title="AutoRAG 통합 비교",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    # 스타일 조정
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        /* 컬럼 구분선 */
        [data-testid="column"]:first-child {
            border-right: 1px solid #ddd;
            padding-right: 1rem;
        }
        [data-testid="column"]:last-child {
            padding-left: 1rem;
        }
        /* 탭 스타일 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# Dashboard 탭 유틸리티 함수
# ============================================================================


def dict_to_markdown(data: dict, level: int = 1) -> str:
    """dict를 마크다운으로 변환"""
    result = ""
    for key, value in data.items():
        if isinstance(value, dict):
            result += f"{'#' * level} {key}\n\n"
            result += dict_to_markdown(value, level + 1)
        else:
            result += f"- **{key}**: {value}\n"
    return result


def dict_to_markdown_table(
    data: dict, key_column_name: str = "Key", value_column_name: str = "Value"
) -> str:
    """dict를 마크다운 테이블로 변환"""
    result = f"| {key_column_name} | {value_column_name} |\n|------|------|\n"
    for key, value in data.items():
        if isinstance(value, float):
            result += f"| {key} | {value:.4f} |\n"
        else:
            result += f"| {key} | {value} |\n"
    return result


def find_node_dir(trial_dir: str) -> list[str]:
    """trial 디렉토리에서 노드 디렉토리 목록 반환"""
    summary_path = os.path.join(trial_dir, "summary.csv")
    if not os.path.exists(summary_path):
        return []
    trial_summary_df = pd.read_csv(summary_path)
    result_paths = []
    for idx, row in trial_summary_df.iterrows():
        node_line_name = row["node_line_name"]
        node_type = row["node_type"]
        result_paths.append(os.path.join(trial_dir, node_line_name, node_type))
    return result_paths


def get_metric_values(node_summary_df: pd.DataFrame) -> dict:
    """최고 성능 모듈의 메트릭 값 추출"""
    non_metric_column_names = [
        "filename",
        "module_name",
        "module_params",
        "execution_time",
        "average_output_token",
        "is_best",
    ]
    best_row = node_summary_df.loc[node_summary_df["is_best"]].drop(
        columns=non_metric_column_names, errors="ignore"
    )
    if len(best_row) == 0:
        return {}
    return best_row.iloc[0].to_dict()


def make_trial_summary_md(trial_dir: str) -> str:
    """trial 요약 마크다운 생성"""
    markdown_text = f"""## Trial Result Summary
- Trial Directory : `{trial_dir}`

"""
    node_dirs = find_node_dir(trial_dir)
    for node_dir in node_dirs:
        node_summary_filepath = os.path.join(node_dir, "summary.csv")
        node_type = os.path.basename(node_dir)
        if not os.path.exists(node_summary_filepath):
            continue
        node_summary_df = pd.read_csv(node_summary_filepath)
        best_rows = node_summary_df.loc[node_summary_df["is_best"]]
        if len(best_rows) == 0:
            continue
        best_row = best_rows.iloc[0]
        metric_dict = get_metric_values(node_summary_df)

        try:
            params_str = str(best_row["module_params"])
            params_dict = ast.literal_eval(params_str) if params_str != "nan" else {}
            params_md = dict_to_markdown(params_dict, level=4)
        except:
            params_md = str(best_row.get("module_params", "N/A"))

        markdown_text += f"""---

### {node_type} best module

**Module Name**: `{best_row["module_name"]}`

**Module Params**:
{params_md}

**Metric Values**:
{dict_to_markdown_table(metric_dict, key_column_name="metric_name", value_column_name="metric_value")}

"""
    return markdown_text


def yaml_to_markdown(yaml_filepath: str) -> str:
    """YAML 파일을 마크다운으로 변환"""
    if not os.path.exists(yaml_filepath):
        return f"File not found: {yaml_filepath}"
    with open(yaml_filepath, "r", encoding="utf-8") as file:
        try:
            content = yaml.safe_load(file)
            return f"```yaml\n{yaml.safe_dump(content, allow_unicode=True)}\n```"
        except yaml.YAMLError as exc:
            return f"Error parsing YAML: {exc}"


# ============================================================================
# Dashboard 탭 - 용어 설명
# ============================================================================


def render_glossary():
    """용어 설명 섹션 렌더링"""
    with st.expander("📖 용어 설명 (클릭하여 펼치기)"):
        cols = st.columns(5)
        glossary_items = list(GLOSSARY.items())

        for idx, (key, info) in enumerate(glossary_items):
            col_idx = idx % 5
            with cols[col_idx]:
                if st.button(
                    info["term"], key=f"glossary_{key}", use_container_width=True
                ):
                    st.session_state.selected_glossary = key

        st.divider()

        if (
            "selected_glossary" in st.session_state
            and st.session_state.selected_glossary
        ):
            info = GLOSSARY[st.session_state.selected_glossary]
            st.markdown(f"### {info['term']}")
            st.markdown(info["detail"])
        else:
            st.info("위 버튼을 클릭하면 상세 설명이 여기에 표시됩니다.")


# ============================================================================
# Dashboard 탭 - 노드 뷰
# ============================================================================


def render_node_view(node_dir: str, key_prefix: str):
    """노드 상세 뷰 (차트 + 테이블)"""
    import matplotlib.pyplot as plt
    import seaborn as sns

    non_metric_column_names = [
        "filename",
        "module_name",
        "module_params",
        "execution_time",
        "average_output_token",
        "is_best",
    ]
    summary_path = os.path.join(node_dir, "summary.csv")
    if not os.path.exists(summary_path):
        st.warning(f"Summary not found: {summary_path}")
        return

    summary_df = pd.read_csv(summary_path)

    # 차트 표시
    try:
        metric_df = summary_df.drop(columns=non_metric_column_names, errors="ignore")

        if not metric_df.empty and len(metric_df.columns) > 0:
            st.markdown("#### Summary distribution plot")

            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots(figsize=(6, 3))
                sns.stripplot(data=metric_df, ax=ax)
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

            with col2:
                fig, ax = plt.subplots(figsize=(6, 3))
                sns.boxplot(data=metric_df, ax=ax)
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
    except Exception as e:
        st.warning(f"차트 생성 오류: {e}")

    # Summary DataFrame 표시
    st.markdown("#### Summary DataFrame")
    st.dataframe(summary_df, use_container_width=True)

    # Module Result DataFrame (선택 가능)
    st.markdown("#### Module Result DataFrame")
    parquet_files = [f for f in os.listdir(node_dir) if f.endswith(".parquet")]
    if parquet_files:
        selected_file = st.selectbox(
            "모듈 결과 파일 선택",
            options=parquet_files,
            key=f"{key_prefix}_module_select",
        )
        if selected_file:
            try:
                module_df = pd.read_parquet(os.path.join(node_dir, selected_file))
                st.dataframe(module_df, use_container_width=True)
            except Exception as e:
                st.error(f"파일 로드 오류: {e}")
    else:
        st.info("모듈 결과 파일이 없습니다.")


# ============================================================================
# Dashboard 탭 - 테스트 케이스 패널
# ============================================================================


def render_testcase_dashboard(testcase_name: str, col_key: str):
    """단일 테스트 케이스의 대시보드 렌더링"""
    tc = load_testcase(testcase_name)
    trial_dir = f"{tc.trial_dir}/0"

    if not os.path.exists(f"{trial_dir}/summary.csv"):
        st.warning(
            f"테스트 케이스 '{testcase_name}'의 결과가 없습니다.\n"
            f"먼저 실행하세요: `make run-testcase TESTCASE={testcase_name}`"
        )
        return

    # 테스트 케이스 기본 정보
    st.markdown(
        f"""### {testcase_name}
*{tc.description}*

| 항목 | 값 |
|------|---|
| 입력 | `{tc.input_dir}` |
| 청크 크기 | {tc.chunk_size} |
| QA 개수 | {tc.num_qa} |
"""
    )

    # 서브탭 구성
    sub_tabs = ["Summary"]
    node_dirs = find_node_dir(trial_dir)
    for node_dir in node_dirs:
        sub_tabs.append(os.path.basename(node_dir))
    sub_tabs.extend(["QA", "Config"])

    selected_tab = st.radio(
        "View", options=sub_tabs, horizontal=True, key=f"{col_key}_subtab"
    )

    st.divider()

    if selected_tab == "Summary":
        # Trial Summary
        trial_summary_md = make_trial_summary_md(trial_dir)
        st.markdown(trial_summary_md)

    elif selected_tab == "QA":
        # QA Data
        qa_filepath = os.path.join(os.path.dirname(trial_dir), "data", "qa.parquet")
        if os.path.exists(qa_filepath):
            try:
                qa_df = pd.read_parquet(qa_filepath)
                st.markdown(f"## QA 데이터\n\n총 {len(qa_df)}개의 질의-응답 쌍")

                for idx, row in qa_df.iterrows():
                    with st.expander(f"Q{idx+1}: {row['query'][:50]}..."):
                        st.markdown(f"**질문:** {row['query']}")
                        if "generation_gt" in row and row["generation_gt"]:
                            gt = row["generation_gt"]
                            if isinstance(gt, list):
                                gt = gt[0] if gt else ""
                            st.markdown(f"**정답:** {gt}")
            except Exception as e:
                st.error(f"QA 데이터 로드 오류: {e}")
        else:
            st.info("QA 데이터를 찾을 수 없습니다.")

    elif selected_tab == "Config":
        # YAML Config
        yaml_filepath = os.path.join(trial_dir, "config.yaml")
        if os.path.exists(yaml_filepath):
            st.markdown("## Config YAML")
            st.markdown(yaml_to_markdown(yaml_filepath))
        else:
            st.info("Config YAML not found")

    else:
        # Node View
        for node_dir in node_dirs:
            if os.path.basename(node_dir) == selected_tab:
                render_node_view(node_dir, f"{col_key}_{selected_tab}")
                break


# ============================================================================
# Dashboard 탭 메인
# ============================================================================


def render_compare_dashboard_tab(testcase_options: dict):
    """평가 결과 비교 탭 렌더링"""
    st.markdown("두 테스트 케이스의 **평가 결과**를 나란히 비교합니다.")

    # 용어 설명
    render_glossary()

    st.divider()

    # 좌우 분할
    left_col, right_col = st.columns(2)
    option_keys = list(testcase_options.keys())
    option_values = list(testcase_options.values())

    with left_col:
        st.subheader("📌 테스트 케이스 A")
        left_select = st.selectbox(
            "테스트 케이스 선택",
            options=option_keys,
            index=0,
            key="dashboard_left_select",
        )
        left_testcase = testcase_options[left_select]
        render_testcase_dashboard(left_testcase, "dashboard_left")

    with right_col:
        st.subheader("📌 테스트 케이스 B")
        right_select = st.selectbox(
            "테스트 케이스 선택",
            options=option_keys,
            index=min(1, len(option_keys) - 1),
            key="dashboard_right_select",
        )
        right_testcase = testcase_options[right_select]
        render_testcase_dashboard(right_testcase, "dashboard_right")


# ============================================================================
# QA Test 탭 (채팅 비교)
# ============================================================================


def create_chat_column(col_key: str, testcase_options: dict, default_idx: int = 0):
    """채팅 컬럼 생성"""
    option_keys = list(testcase_options.keys())

    # 테스트 케이스 선택
    selected_display = st.selectbox(
        "테스트 케이스 선택",
        options=option_keys,
        index=default_idx,
        key=f"{col_key}_testcase_select",
    )
    selected_testcase = testcase_options[selected_display]

    # 선택된 테스트 케이스 정보
    tc = load_testcase(selected_testcase)
    st.caption(f"청크: {tc.chunk_size} | QA: {tc.num_qa}")

    # 세션 키
    runner_key = f"{col_key}_runner"
    messages_key = f"{col_key}_messages"
    current_tc_key = f"{col_key}_current_tc"

    # 테스트 케이스 변경 시 초기화
    if current_tc_key not in st.session_state:
        st.session_state[current_tc_key] = selected_testcase
    elif st.session_state[current_tc_key] != selected_testcase:
        st.session_state[current_tc_key] = selected_testcase
        st.session_state[messages_key] = []
        if runner_key in st.session_state:
            st.session_state[runner_key] = None
        st.rerun()

    # Runner 초기화
    if runner_key not in st.session_state or st.session_state[runner_key] is None:
        trial_path = f"{tc.trial_dir}/0"
        if os.path.exists(trial_path):
            try:
                with st.spinner("RAG 파이프라인 로딩 중..."):
                    st.session_state[runner_key] = get_runner(trial_path)
                st.success("로드 완료!", icon="✅")
            except Exception as e:
                st.error(f"로드 실패: {e}")
                return
        else:
            st.error(f"Trial 없음: {trial_path}")
            return

    # 메시지 초기화
    if messages_key not in st.session_state:
        st.session_state[messages_key] = []

    # 채팅 컨테이너
    chat_container = st.container(height=400)

    # 채팅 히스토리 표시
    with chat_container:
        for message in st.session_state[messages_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 사용자 입력
    if query := st.chat_input("질문을 입력하세요...", key=f"{col_key}_chat_input"):
        # 사용자 메시지 추가
        st.session_state[messages_key].append({"role": "user", "content": query})

        # RAG 응답 생성
        try:
            result = st.session_state[runner_key].run(query)

            # result 처리
            if isinstance(result, str):
                answer = result
            elif isinstance(result, dict):
                answer = result.get("answer", "응답을 생성할 수 없습니다.")
                retrieved_docs = result.get("retrieved_contents", [])
                if retrieved_docs:
                    answer += "\n\n---\n**참조:**\n"
                    for i, doc in enumerate(retrieved_docs[:2], 1):
                        doc_preview = doc[:150] + "..." if len(doc) > 150 else doc
                        answer += f"\n{i}. {doc_preview}\n"
            else:
                answer = str(result)

            st.session_state[messages_key].append(
                {"role": "assistant", "content": answer}
            )
        except Exception as e:
            error_msg = f"오류: {e}"
            st.session_state[messages_key].append(
                {"role": "assistant", "content": error_msg}
            )

        st.rerun()


def render_compare_web_tab(testcase_options: dict):
    """질의 비교 탭 렌더링"""
    st.markdown("두 테스트 케이스에 **동일한 질문**을 비교합니다.")

    # 동일 질문 입력 (상단)
    sync_query = st.text_input(
        "🔗 동시 질문 (양쪽에 동일한 질문 전송)",
        placeholder="양쪽 테스트 케이스에 동일한 질문을 보내려면 여기에 입력하세요...",
        key="sync_query_input",
    )

    if st.button("양쪽에 질문 보내기", disabled=not sync_query):
        # 양쪽 메시지에 추가
        for col_key in ["left", "right"]:
            messages_key = f"{col_key}_messages"
            runner_key = f"{col_key}_runner"

            if messages_key not in st.session_state:
                st.session_state[messages_key] = []

            st.session_state[messages_key].append(
                {"role": "user", "content": sync_query}
            )

            # RAG 응답 생성
            if runner_key in st.session_state and st.session_state[runner_key]:
                try:
                    result = st.session_state[runner_key].run(sync_query)
                    if isinstance(result, str):
                        answer = result
                    elif isinstance(result, dict):
                        answer = result.get("answer", "응답 없음")
                    else:
                        answer = str(result)
                    st.session_state[messages_key].append(
                        {"role": "assistant", "content": answer}
                    )
                except Exception as e:
                    st.session_state[messages_key].append(
                        {"role": "assistant", "content": f"오류: {e}"}
                    )

        st.rerun()

    st.divider()

    # 좌우 분할
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📌 테스트 케이스 A")
        create_chat_column("left", testcase_options, default_idx=0)

    with right_col:
        st.subheader("📌 테스트 케이스 B")
        create_chat_column(
            "right", testcase_options, default_idx=min(1, len(testcase_options) - 1)
        )


# ============================================================================
# 메인
# ============================================================================


def main():
    set_page_config()

    st.title("🔄 AutoRAG 통합 비교")
    st.markdown("테스트 케이스 비교를 위한 통합 인터페이스")

    available = find_available_testcases()

    if len(available) < 2:
        st.warning(
            f"비교하려면 최소 2개의 실행된 테스트 케이스가 필요합니다. "
            f"현재 {len(available)}개만 있습니다.\n\n"
            "테스트 케이스 실행:\n```\nmake run-testcase TESTCASE=hr_rule\n```"
        )
        return

    # 선택 옵션 생성
    testcase_options = {f"{name} - {desc}": name for name, desc in available}

    # 상단 탭
    tab1, tab2 = st.tabs(["📊 Compare Dashboard", "💬 QA Test"])

    with tab1:
        render_compare_dashboard_tab(testcase_options)

    with tab2:
        render_compare_web_tab(testcase_options)


if __name__ == "__main__":
    main()
