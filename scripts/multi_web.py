#!/usr/bin/env python3
"""
멀티 테스트 케이스 웹 인터페이스

테스트 케이스를 선택하여 RAG 질의를 수행할 수 있는 웹 인터페이스입니다.

사용법:
    streamlit run scripts/multi_web.py

    또는 Makefile:
    make multi-web
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
        page_title="AutoRAG Multi-TestCase",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def main():
    set_page_config()

    st.title("🤖 AutoRAG 멀티 테스트 케이스")
    st.markdown("테스트 케이스를 선택하고 질문을 입력하세요.")

    # 사이드바에 테스트 케이스 선택
    with st.sidebar:
        st.header("테스트 케이스 선택")

        available = find_available_testcases()

        if not available:
            st.warning(
                "실행된 테스트 케이스가 없습니다.\n\n"
                "테스트 케이스를 실행하려면:\n"
                "```\nmake run-testcase TESTCASE=인사규정\n```"
            )
            return

        # 테스트 케이스 선택
        testcase_options = {f"{name} - {desc}": name for name, desc in available}
        selected_display = st.selectbox(
            "테스트 케이스",
            options=list(testcase_options.keys()),
            key="testcase_select",
        )
        selected_testcase = testcase_options[selected_display]

        # 선택된 테스트 케이스 정보
        tc = load_testcase(selected_testcase)
        st.markdown("---")
        st.markdown(f"**설명**: {tc.description}")
        st.markdown(f"**청크 크기**: {tc.chunk_size}")
        st.markdown(f"**QA 개수**: {tc.num_qa}")

        # 테스트 케이스 변경 시 세션 초기화
        if "current_testcase" not in st.session_state:
            st.session_state.current_testcase = selected_testcase
        elif st.session_state.current_testcase != selected_testcase:
            st.session_state.current_testcase = selected_testcase
            st.session_state.messages = []
            st.session_state.runner = None
            st.rerun()

    # Runner 초기화
    if "runner" not in st.session_state or st.session_state.runner is None:
        trial_path = f"{tc.trial_dir}/0"
        if os.path.exists(trial_path):
            try:
                with st.spinner("RAG 파이프라인 로딩 중..."):
                    st.session_state.runner = get_runner(trial_path)
                st.success("파이프라인 로드 완료!")
            except Exception as e:
                st.error(f"파이프라인 로드 실패: {e}")
                return
        else:
            st.error(f"Trial 경로가 없습니다: {trial_path}")
            return

    # 메시지 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력
    if query := st.chat_input("질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # RAG 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                try:
                    result = st.session_state.runner.run(query)
                    answer = result.get("answer", "응답을 생성할 수 없습니다.")

                    # 검색된 문서 정보
                    retrieved_docs = result.get("retrieved_contents", [])
                    if retrieved_docs:
                        answer += "\n\n---\n**참조 문서:**\n"
                        for i, doc in enumerate(retrieved_docs[:3], 1):
                            doc_preview = doc[:200] + "..." if len(doc) > 200 else doc
                            answer += f"\n{i}. {doc_preview}\n"

                    st.markdown(answer)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                except Exception as e:
                    error_msg = f"오류 발생: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )


if __name__ == "__main__":
    main()
