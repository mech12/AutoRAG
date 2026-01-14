#!/usr/bin/env python3
"""
테스트 케이스 비교 웹 인터페이스

두 개의 테스트 케이스를 나란히 비교하며 질의할 수 있는 웹 인터페이스입니다.

사용법:
    streamlit run scripts/compare_web.py

    또는 Makefile:
    make compare-web
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from testcase_config import list_testcases, load_testcase


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
        page_title="AutoRAG Compare Web",
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
        </style>
        """,
        unsafe_allow_html=True,
    )


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

            st.session_state[messages_key].append({"role": "assistant", "content": answer})
        except Exception as e:
            error_msg = f"오류: {e}"
            st.session_state[messages_key].append({"role": "assistant", "content": error_msg})

        st.rerun()


def main():
    set_page_config()

    st.title("🔄 AutoRAG 테스트 케이스 비교")
    st.markdown("두 테스트 케이스를 선택하고 동일한 질문을 비교해보세요.")

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

    # 동일 질문 입력 (상단)
    st.markdown("---")
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

            st.session_state[messages_key].append({"role": "user", "content": sync_query})

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
                    st.session_state[messages_key].append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.session_state[messages_key].append({"role": "assistant", "content": f"오류: {e}"})

        st.rerun()

    st.markdown("---")

    # 좌우 분할
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📌 테스트 케이스 A")
        create_chat_column("left", testcase_options, default_idx=0)

    with right_col:
        st.subheader("📌 테스트 케이스 B")
        create_chat_column("right", testcase_options, default_idx=min(1, len(testcase_options) - 1))


if __name__ == "__main__":
    main()
