#!/usr/bin/env python3
"""
테스트 케이스 비교 대시보드

두 개의 테스트 케이스를 좌우로 나란히 비교할 수 있는 대시보드입니다.

사용법:
    python scripts/compare_dashboard.py [--port 7691]

    또는 Makefile:
    make compare-dashboard
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add scripts directory and project root to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import pandas as pd
import panel as pn
import seaborn as sns
import yaml
from bokeh.models import NumberFormatter, BooleanFormatter
from testcase_config import list_testcases, load_testcase

# Panel 확장 초기화
pn.extension(
    "tabulator",
    "mathjax",
    console_output="disable",
    sizing_mode="stretch_width",
    css_files=[
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"
    ],
)

# 커스텀 CSS
CSS = """
.compare-panel {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px;
    margin: 5px;
}
.bk-root .bk-tabs-header .bk-tab {
    font-size: 12px;
}
"""


# --- dashboard.py 함수들 (autorag 모듈 의존성 없이 직접 복사) ---

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


def dict_to_markdown_table(data: dict, key_column_name: str = "Key", value_column_name: str = "Value") -> str:
    """dict를 마크다운 테이블로 변환"""
    result = f"| {key_column_name} | {value_column_name} |\n|------|------|\n"
    for key, value in data.items():
        if isinstance(value, float):
            result += f"| {key} | {value:.4f} |\n"
        else:
            result += f"| {key} | {value} |\n"
    return result


def find_node_dir(trial_dir: str) -> List[str]:
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


def get_metric_values(node_summary_df: pd.DataFrame) -> Dict:
    """최고 성능 모듈의 메트릭 값 추출"""
    non_metric_column_names = [
        "filename", "module_name", "module_params",
        "execution_time", "average_output_token", "is_best",
    ]
    best_row = node_summary_df.loc[node_summary_df["is_best"]].drop(
        columns=non_metric_column_names, errors="ignore"
    )
    if len(best_row) == 0:
        return {}
    return best_row.iloc[0].to_dict()


def make_trial_summary_md(trial_dir: str) -> str:
    """trial 요약 마크다운 생성"""
    markdown_text = f"""# Trial Result Summary
- Trial Directory : {trial_dir}

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
        markdown_text += f"""---

## {node_type} best module

### Module Name

{best_row["module_name"]}

### Module Params

{dict_to_markdown(ast.literal_eval(str(best_row["module_params"])), level=3)}

### Metric Values

{dict_to_markdown_table(metric_dict, key_column_name="metric_name", value_column_name="metric_value")}

"""
    return markdown_text


def node_view(node_dir: str) -> pn.Column:
    """노드 상세 뷰 (차트 + 테이블)"""
    non_metric_column_names = [
        "filename", "module_name", "module_params",
        "execution_time", "average_output_token", "is_best",
    ]
    summary_path = os.path.join(node_dir, "summary.csv")
    if not os.path.exists(summary_path):
        return pn.Column(pn.pane.Markdown(f"Summary not found: {summary_path}"))

    summary_df = pd.read_csv(summary_path)
    bokeh_formatters = {
        "float": NumberFormatter(format="0.000"),
        "bool": BooleanFormatter(),
    }

    first_parquet = os.path.join(node_dir, "0.parquet")
    if os.path.exists(first_parquet):
        first_df = pd.read_parquet(first_parquet, engine="pyarrow")
    else:
        first_df = pd.DataFrame()

    each_module_df_widget = pn.widgets.Tabulator(
        pd.DataFrame(columns=first_df.columns) if not first_df.empty else pd.DataFrame(),
        name="Module DataFrame",
        formatters=bokeh_formatters,
        pagination="local",
        page_size=20,
        widths=150,
    )

    def change_module_widget(event):
        if event.column == "detail":
            filename = summary_df["filename"].iloc[event.row]
            filepath = os.path.join(node_dir, filename)
            if os.path.exists(filepath):
                each_module_df = pd.read_parquet(filepath, engine="pyarrow")
                each_module_df_widget.value = each_module_df

    df_widget = pn.widgets.Tabulator(
        summary_df,
        name="Summary DataFrame",
        formatters=bokeh_formatters,
        buttons={"detail": '<i class="fa fa-eye"></i>'},
        widths=150,
    )
    df_widget.on_click(change_module_widget)

    try:
        fig, ax = plt.subplots(figsize=(8, 4))
        metric_df = summary_df.drop(columns=non_metric_column_names, errors="ignore")
        sns.stripplot(data=metric_df, ax=ax)
        plt.xticks(rotation=45, ha='right')
        strip_plot_pane = pn.pane.Matplotlib(fig, tight=True)
        plt.close(fig)

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.boxplot(data=metric_df, ax=ax2)
        plt.xticks(rotation=45, ha='right')
        box_plot_pane = pn.pane.Matplotlib(fig2, tight=True)
        plt.close(fig2)

        plot_pane = pn.Row(strip_plot_pane, box_plot_pane)

        layout = pn.Column(
            "## Summary distribution plot",
            plot_pane,
            "## Summary DataFrame",
            df_widget,
            "## Module Result DataFrame",
            each_module_df_widget,
        )
    except Exception as e:
        layout = pn.Column(
            f"## Error creating plots: {e}",
            "## Summary DataFrame",
            df_widget,
        )

    return layout


def yaml_to_markdown(yaml_filepath: str) -> str:
    """YAML 파일을 마크다운으로 변환"""
    if not os.path.exists(yaml_filepath):
        return f"File not found: {yaml_filepath}"
    with open(yaml_filepath, "r", encoding="utf-8") as file:
        try:
            content = yaml.safe_load(file)
            return f"## {os.path.basename(yaml_filepath)}\n```yaml\n{yaml.safe_dump(content, allow_unicode=True)}\n```\n\n"
        except yaml.YAMLError as exc:
            return f"Error parsing YAML: {exc}"


# --- 비교 대시보드 함수들 ---

def find_available_testcases() -> list[tuple[str, str]]:
    """실행된 테스트 케이스 목록 반환 (trial 결과가 있는 것만)"""
    available = []
    for name, desc in list_testcases():
        tc = load_testcase(name)
        trial_summary = f"{tc.trial_dir}/0/summary.csv"
        if os.path.exists(trial_summary):
            available.append((name, desc))
    return available


def create_testcase_panel(testcase_name: str) -> pn.Column:
    """
    단일 테스트 케이스의 대시보드 패널 생성
    """
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

    # 테스트 케이스 기본 정보
    info_md = f"""### {testcase_name}
*{tc.description}*

| 항목 | 값 |
|------|---|
| 입력 | `{tc.input_dir}` |
| 청크 크기 | {tc.chunk_size} |
| QA 개수 | {tc.num_qa} |
"""

    # Trial Summary (dashboard.py 함수 재사용)
    trial_summary_md = make_trial_summary_md(trial_dir)
    trial_summary_tab = pn.pane.Markdown(trial_summary_md, sizing_mode="stretch_width")

    # Node Views (dashboard.py 함수 재사용)
    node_views = []
    for node_dir in find_node_dir(trial_dir):
        node_name = str(os.path.basename(node_dir))
        try:
            node_views.append((node_name, node_view(node_dir)))
        except Exception as e:
            node_views.append((node_name, pn.pane.Markdown(f"Error: {e}")))

    # YAML Config
    yaml_filepath = os.path.join(trial_dir, "config.yaml")
    if os.path.exists(yaml_filepath):
        yaml_md = yaml_to_markdown(yaml_filepath)
        yaml_tab = pn.pane.Markdown(yaml_md, sizing_mode="stretch_width")
    else:
        yaml_tab = pn.pane.Markdown("Config YAML not found")

    # Tabs 구성
    tabs = pn.Tabs(
        ("Summary", trial_summary_tab),
        *node_views,
        ("Config", yaml_tab),
        dynamic=True,
    )

    return pn.Column(
        pn.pane.Markdown(info_md),
        tabs,
        css_classes=["compare-panel"],
        sizing_mode="stretch_both",
    )


def create_compare_app():
    """비교 대시보드 앱 생성"""
    available = find_available_testcases()

    if len(available) < 1:
        return pn.Column(
            pn.pane.Markdown("# AutoRAG 테스트 케이스 비교"),
            pn.pane.Alert(
                "실행된 테스트 케이스가 없습니다.\n\n"
                "테스트 케이스를 실행하려면:\n"
                "```\nmake run-testcase TESTCASE=인사규정\n```",
                alert_type="warning",
            ),
        )

    if len(available) < 2:
        return pn.Column(
            pn.pane.Markdown("# AutoRAG 테스트 케이스 비교"),
            pn.pane.Alert(
                "비교하려면 최소 2개의 실행된 테스트 케이스가 필요합니다.\n"
                f"현재 {len(available)}개만 있습니다.",
                alert_type="warning",
            ),
        )

    # 선택 옵션 생성 (key: 표시명, value: 테스트케이스 이름)
    testcase_options = {f"{name} - {desc}": name for name, desc in available}
    option_values = list(testcase_options.values())

    # 좌측 Select
    left_select = pn.widgets.Select(
        name="좌측 테스트 케이스",
        options=testcase_options,
        value=option_values[0],
        sizing_mode="stretch_width",
    )

    # 우측 Select (다른 기본값)
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
        pn.Column(
            left_select,
            left_content,
            sizing_mode="stretch_both",
        ),
        pn.layout.VSpacer(width=10),
        pn.Column(
            right_select,
            right_content,
            sizing_mode="stretch_both",
        ),
        sizing_mode="stretch_both",
    )

    return pn.Column(
        pn.pane.Markdown("# AutoRAG 테스트 케이스 비교"),
        pn.pane.Markdown("두 테스트 케이스의 평가 결과를 나란히 비교합니다."),
        pn.layout.Divider(),
        comparison_row,
        sizing_mode="stretch_both",
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoRAG TestCase Compare Dashboard")
    parser.add_argument("--port", type=int, default=7691, help="Port number (default: 7691)")
    args = parser.parse_args()

    app = create_compare_app()

    template = pn.template.FastListTemplate(
        site="AutoRAG",
        title="Compare Dashboard",
        main=[app],
        raw_css=[CSS],
    )

    print(f"Starting Compare Dashboard on http://localhost:{args.port}")
    template.show(port=args.port)


if __name__ == "__main__":
    main()
