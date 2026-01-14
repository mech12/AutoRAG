#!/usr/bin/env python3
"""
AutoRAG 통합 대시보드

두 개의 탭으로 구성:
1. Compare Dashboard: 두 테스트 케이스의 평가 결과 비교
2. Compare Web: 두 테스트 케이스에 동일한 질문을 비교

사용법:
    python scripts/unified_dashboard.py --port 7700

    또는 Makefile:
    make unified-dashboard
"""

import argparse
import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

import panel as pn
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from testcase_config import list_testcases, load_testcase

# Panel 확장 설정
pn.extension("tabulator", sizing_mode="stretch_width")

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


# ============================================================================
# Compare Dashboard 탭 (평가 결과 비교)
# ============================================================================

# Import from compare_dashboard.py
from compare_dashboard import (
    create_testcase_panel,
    create_glossary_panel,
)


def create_compare_dashboard_tab():
    """평가 결과 비교 탭 생성"""
    available = find_available_testcases()

    if len(available) < 2:
        return pn.Column(
            pn.pane.Alert(
                f"비교하려면 최소 2개의 실행된 테스트 케이스가 필요합니다. "
                f"현재 {len(available)}개만 있습니다.",
                alert_type="warning",
            ),
        )

    # 선택 옵션 생성
    testcase_options = {f"{name} - {desc}": name for name, desc in available}
    option_values = list(testcase_options.values())

    # 좌측 Select
    left_select = pn.widgets.Select(
        name="좌측 테스트 케이스",
        options=testcase_options,
        value=option_values[0],
        sizing_mode="stretch_width",
    )

    # 우측 Select
    right_select = pn.widgets.Select(
        name="우측 테스트 케이스",
        options=testcase_options,
        value=option_values[1] if len(option_values) > 1 else option_values[0],
        sizing_mode="stretch_width",
    )

    # 콘텐츠 영역
    left_content = pn.Column(sizing_mode="stretch_both")
    right_content = pn.Column(sizing_mode="stretch_both")

    def update_left(event):
        left_content.clear()
        if left_select.value:
            left_content.append(create_testcase_panel(left_select.value))

    def update_right(event):
        right_content.clear()
        if right_select.value:
            right_content.append(create_testcase_panel(right_select.value))

    left_select.param.watch(update_left, "value")
    right_select.param.watch(update_right, "value")

    # 초기 로드
    if left_select.value:
        left_content.append(create_testcase_panel(left_select.value))
    if right_select.value:
        right_content.append(create_testcase_panel(right_select.value))

    # 좌우 분할 레이아웃
    comparison_row = pn.Row(
        pn.Column(left_select, left_content, sizing_mode="stretch_both"),
        pn.layout.VSpacer(width=10),
        pn.Column(right_select, right_content, sizing_mode="stretch_both"),
        sizing_mode="stretch_both",
    )

    # 용어 설명
    glossary_accordion = pn.Accordion(
        ("📖 용어 설명", create_glossary_panel()),
        active=[],
        sizing_mode="stretch_width",
    )

    return pn.Column(
        pn.pane.Markdown("두 테스트 케이스의 **평가 결과**를 나란히 비교합니다."),
        comparison_row,
        glossary_accordion,
        sizing_mode="stretch_both",
    )


# ============================================================================
# Compare Web 탭 (질의 비교)
# ============================================================================

# Runner 캐시
_runners = {}


def get_cached_runner(testcase_name: str):
    """Runner 캐싱하여 반환"""
    if testcase_name not in _runners:
        tc = load_testcase(testcase_name)
        trial_path = f"{tc.trial_dir}/0"
        if os.path.exists(trial_path):
            _runners[testcase_name] = get_runner(trial_path)
        else:
            return None
    return _runners[testcase_name]


def create_chat_panel(side: str, testcase_options: dict, default_idx: int = 0):
    """채팅 패널 생성"""
    option_keys = list(testcase_options.keys())
    option_values = list(testcase_options.values())

    # 테스트 케이스 선택
    select = pn.widgets.Select(
        name=f"테스트 케이스",
        options=testcase_options,
        value=option_values[default_idx],
        sizing_mode="stretch_width",
    )

    # 상태 표시
    status = pn.pane.Markdown("", sizing_mode="stretch_width")

    # 채팅 히스토리
    chat_history = pn.Column(
        sizing_mode="stretch_both",
        scroll=True,
        height=350,
        styles={"background": "#f8f9fa", "border-radius": "5px", "padding": "10px"},
    )

    # 입력 필드
    input_field = pn.widgets.TextInput(
        placeholder="질문을 입력하세요...",
        sizing_mode="stretch_width",
    )

    # 전송 버튼
    send_button = pn.widgets.Button(name="전송", button_type="primary", width=80)

    def add_message(role: str, content: str):
        """채팅 메시지 추가"""
        if role == "user":
            msg = pn.pane.Markdown(
                f"**🧑 질문:** {content}",
                styles={"background": "#e3f2fd", "padding": "8px", "border-radius": "5px", "margin": "5px 0"},
            )
        else:
            msg = pn.pane.Markdown(
                f"**🤖 답변:** {content}",
                styles={"background": "#fff", "padding": "8px", "border-radius": "5px", "margin": "5px 0"},
            )
        chat_history.append(msg)

    def send_message(event=None):
        """메시지 전송"""
        query = input_field.value.strip()
        if not query:
            return

        testcase_name = select.value
        if not testcase_name:
            return

        # 사용자 메시지 추가
        add_message("user", query)
        input_field.value = ""

        # RAG 응답 생성
        try:
            runner = get_cached_runner(testcase_name)
            if runner is None:
                add_message("assistant", "Runner를 로드할 수 없습니다.")
                return

            status.object = "⏳ 답변 생성 중..."
            result = runner.run(query)

            if isinstance(result, str):
                answer = result
            elif isinstance(result, dict):
                answer = result.get("answer", "응답 없음")
            else:
                answer = str(result)

            add_message("assistant", answer)
            status.object = ""

        except Exception as e:
            add_message("assistant", f"오류: {e}")
            status.object = ""

    send_button.on_click(send_message)
    input_field.param.watch(lambda e: send_message() if e.new == "" else None, "value_input")

    # Enter 키로 전송
    input_field.param.watch(
        lambda e: send_message() if e.obj.value and e.new else None,
        "value",
    )

    def on_select_change(event):
        """테스트 케이스 변경 시"""
        chat_history.clear()
        testcase_name = event.new
        if testcase_name:
            tc = load_testcase(testcase_name)
            status.object = f"📁 {tc.description}"
            # 미리 Runner 로드
            try:
                status.object = "⏳ 파이프라인 로딩..."
                get_cached_runner(testcase_name)
                status.object = f"✅ 준비 완료"
            except Exception as e:
                status.object = f"❌ 로드 실패: {e}"

    select.param.watch(on_select_change, "value")

    # 초기 로드
    if select.value:
        tc = load_testcase(select.value)
        status.object = f"📁 {tc.description}"

    return pn.Column(
        select,
        status,
        chat_history,
        pn.Row(input_field, send_button),
        sizing_mode="stretch_both",
    ), input_field, select


def create_compare_web_tab():
    """질의 비교 탭 생성"""
    available = find_available_testcases()

    if len(available) < 2:
        return pn.Column(
            pn.pane.Alert(
                f"비교하려면 최소 2개의 실행된 테스트 케이스가 필요합니다. "
                f"현재 {len(available)}개만 있습니다.",
                alert_type="warning",
            ),
        )

    # 선택 옵션 생성
    testcase_options = {f"{name} - {desc}": name for name, desc in available}

    # 좌우 채팅 패널 생성
    left_panel, left_input, left_select = create_chat_panel("left", testcase_options, 0)
    right_panel, right_input, right_select = create_chat_panel("right", testcase_options, min(1, len(testcase_options) - 1))

    # 동시 질문 입력
    sync_input = pn.widgets.TextInput(
        placeholder="양쪽에 동일한 질문을 보내려면 여기에 입력하세요...",
        sizing_mode="stretch_width",
    )
    sync_button = pn.widgets.Button(name="🔗 양쪽에 질문 보내기", button_type="success")

    def send_sync_message(event):
        """양쪽에 동일한 질문 전송"""
        query = sync_input.value.strip()
        if not query:
            return

        # 양쪽 입력 필드에 질문 설정 후 전송
        left_input.value = query
        right_input.value = query
        sync_input.value = ""

    sync_button.on_click(send_sync_message)

    # 레이아웃
    sync_row = pn.Row(
        sync_input,
        sync_button,
        sizing_mode="stretch_width",
    )

    comparison_row = pn.Row(
        pn.Column(
            pn.pane.Markdown("### 📌 테스트 케이스 A"),
            left_panel,
            sizing_mode="stretch_both",
        ),
        pn.layout.VSpacer(width=10),
        pn.Column(
            pn.pane.Markdown("### 📌 테스트 케이스 B"),
            right_panel,
            sizing_mode="stretch_both",
        ),
        sizing_mode="stretch_both",
    )

    return pn.Column(
        pn.pane.Markdown("두 테스트 케이스에 **동일한 질문**을 비교합니다."),
        sync_row,
        pn.layout.Divider(),
        comparison_row,
        sizing_mode="stretch_both",
    )


# ============================================================================
# 메인 앱
# ============================================================================

def create_unified_app():
    """통합 대시보드 앱 생성"""
    # 상단 탭
    tabs = pn.Tabs(
        ("📊 Compare Dashboard", create_compare_dashboard_tab()),
        ("💬 Compare Web", create_compare_web_tab()),
        dynamic=True,
        tabs_location="above",
    )

    # 전체 레이아웃
    app = pn.Column(
        pn.pane.Markdown(
            "# 🔄 AutoRAG 통합 대시보드\n"
            "테스트 케이스 비교를 위한 통합 인터페이스",
            sizing_mode="stretch_width",
        ),
        tabs,
        sizing_mode="stretch_both",
    )

    return app


def main():
    parser = argparse.ArgumentParser(description="AutoRAG 통합 대시보드")
    parser.add_argument("--port", type=int, default=7700, help="서버 포트 (기본값: 7700)")
    args = parser.parse_args()

    app = create_unified_app()

    print(f"\n{'='*60}")
    print("AutoRAG 통합 대시보드")
    print(f"{'='*60}")
    print(f"URL: http://localhost:{args.port}")
    print(f"{'='*60}\n")

    pn.serve(
        app,
        port=args.port,
        title="AutoRAG Unified Dashboard",
        show=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()
