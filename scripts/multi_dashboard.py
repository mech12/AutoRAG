#!/usr/bin/env python3
"""
멀티 테스트 케이스 대시보드

테스트 케이스를 선택하여 평가 결과를 조회할 수 있는 대시보드입니다.

사용법:
    python scripts/multi_dashboard.py [--port 7690]

    또는 Makefile:
    make multi-dashboard
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

import panel as pn
from testcase_config import list_testcases, load_testcase

# Panel 확장 초기화
pn.extension(
    "tabulator",
    sizing_mode="stretch_width",
)

# 테스트 케이스 기본 디렉토리
TESTCASE_BASE_DIR = "logs/testCase"


def find_available_testcases() -> list[tuple[str, str]]:
    """실행된 테스트 케이스 목록 반환 (trial 결과가 있는 것만)"""
    available = []
    for name, desc in list_testcases():
        tc = load_testcase(name)
        trial_summary = f"{tc.trial_dir}/0/summary.csv"
        if os.path.exists(trial_summary):
            available.append((name, desc))
    return available


def create_dashboard_content(testcase_name: str) -> pn.Column:
    """선택된 테스트 케이스의 대시보드 콘텐츠 생성"""
    import pandas as pd

    tc = load_testcase(testcase_name)
    trial_dir = f"{tc.trial_dir}/0"

    if not os.path.exists(f"{trial_dir}/summary.csv"):
        return pn.Column(
            pn.pane.Alert(
                f"테스트 케이스 '{testcase_name}'의 결과가 없습니다.\n"
                f"먼저 실행하세요: make run-testcase TESTCASE={testcase_name}",
                alert_type="warning",
            )
        )

    # Summary 로드
    summary_df = pd.read_csv(f"{trial_dir}/summary.csv")

    # 테스트 케이스 정보
    info_md = f"""
## 테스트 케이스: {testcase_name}

**설명**: {tc.description}

| 항목 | 값 |
|------|---|
| 입력 디렉토리 | `{tc.input_dir}` |
| 청크 크기 | {tc.chunk_size} |
| 청크 오버랩 | {tc.chunk_overlap} |
| QA 개수 | {tc.num_qa} |
| LLM 사용 | {tc.use_llm} |
"""

    # Retrieval 메트릭
    retrieval_md = ""
    retrieval_paths = [
        f"{trial_dir}/retrieve_node_line/semantic_retrieval/summary.csv",
        f"{trial_dir}/retrieve_node_line/lexical_retrieval/summary.csv",
    ]
    for rpath in retrieval_paths:
        if os.path.exists(rpath):
            ret_df = pd.read_csv(rpath)
            if not ret_df.empty:
                retrieval_md = f"""
### Retrieval 메트릭

| 메트릭 | 값 |
|--------|---|
| F1 Score | {ret_df['retrieval_f1'].iloc[0]:.4f} |
| Recall | {ret_df['retrieval_recall'].iloc[0]:.4f} |
| Precision | {ret_df['retrieval_precision'].iloc[0]:.4f} |
"""
            break

    # Generator 메트릭
    generator_md = ""
    gen_path = f"{trial_dir}/post_retrieve_node_line/generator/summary.csv"
    if os.path.exists(gen_path):
        gen_df = pd.read_csv(gen_path)
        if not gen_df.empty and "rouge" in gen_df.columns:
            generator_md = f"""
### Generator 메트릭

| 메트릭 | 값 |
|--------|---|
| ROUGE Score | {gen_df['rouge'].iloc[0]:.4f} |
| 실행 시간 | {gen_df['execution_time'].iloc[0]:.2f}s |
"""

    # Summary 테이블
    summary_table = pn.widgets.Tabulator(
        summary_df,
        sizing_mode="stretch_width",
        height=200,
    )

    return pn.Column(
        pn.pane.Markdown(info_md),
        pn.pane.Markdown(retrieval_md) if retrieval_md else None,
        pn.pane.Markdown(generator_md) if generator_md else None,
        pn.pane.Markdown("### 전체 Summary"),
        summary_table,
    )


def create_app():
    """대시보드 앱 생성"""
    available = find_available_testcases()

    if not available:
        return pn.Column(
            pn.pane.Markdown("# AutoRAG 멀티 대시보드"),
            pn.pane.Alert(
                "실행된 테스트 케이스가 없습니다.\n\n"
                "테스트 케이스를 실행하려면:\n"
                "```\nmake run-testcase TESTCASE=인사규정\n```",
                alert_type="info",
            ),
        )

    # 테스트 케이스 선택 위젯
    testcase_options = {f"{name} - {desc}": name for name, desc in available}
    testcase_select = pn.widgets.Select(
        name="테스트 케이스 선택",
        options=testcase_options,
        sizing_mode="stretch_width",
    )

    # 콘텐츠 영역
    content_area = pn.Column()

    def update_content(event):
        testcase_name = testcase_select.value
        content_area.clear()
        content_area.append(create_dashboard_content(testcase_name))

    testcase_select.param.watch(update_content, "value")

    # 초기 콘텐츠 로드
    if testcase_select.value:
        content_area.append(create_dashboard_content(testcase_select.value))

    return pn.Column(
        pn.pane.Markdown("# AutoRAG 멀티 대시보드"),
        pn.pane.Markdown("테스트 케이스를 선택하여 평가 결과를 확인하세요."),
        testcase_select,
        pn.layout.Divider(),
        content_area,
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoRAG Multi-TestCase Dashboard")
    parser.add_argument("--port", type=int, default=7690, help="Port number")
    args = parser.parse_args()

    app = create_app()

    template = pn.template.FastListTemplate(
        site="AutoRAG",
        title="Multi-TestCase Dashboard",
        main=[app],
    )

    print(f"Starting Multi-Dashboard on http://localhost:{args.port}")
    template.show(port=args.port)


if __name__ == "__main__":
    main()
