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
.glossary-term {
    display: inline-block;
    background: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 4px;
    padding: 4px 8px;
    margin: 2px;
    cursor: pointer;
    font-size: 13px;
}
.glossary-term:hover {
    background: #bbdefb;
}
.glossary-detail {
    background: #f5f5f5;
    border-left: 4px solid #2196f3;
    padding: 12px;
    margin: 8px 0;
    border-radius: 4px;
}
"""

# --- 용어 사전 (docs/note-roy/2026-0113/06-테스트 결과(VectorDB).md 기반) ---
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
```"""
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
```"""
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
```"""
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
```"""
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
| Milvus    | 1.61s |"""
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

**권장값**: 보통 3~10 사이"""
    },
    "semantic_retrieval": {
        "term": "의미 기반 검색",
        "short": "벡터 유사도로 문서 검색",
        "detail": """**의미 기반 검색 (Semantic Retrieval)**

문서와 질문을 벡터(숫자 배열)로 변환 후, 벡터 유사도를 계산하여 관련 문서를 찾는 방식입니다.

**장점**:
- 키워드가 정확히 일치하지 않아도 의미적으로 유사한 문서 검색 가능
- "연차휴가"로 검색해도 "연차유급휴가" 문서를 찾을 수 있음

**사용되는 Vector DB**: Milvus, Weaviate, Qdrant, Chroma 등"""
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

**실행 시간의 대부분**이 이 단계에서 소요됩니다."""
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
```"""
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
| **Chroma** | 설치 간단, 로컬 개발 적합 | 대규모에 부적합 |"""
    },
}


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


# --- 용어 설명 UI 컴포넌트 ---

def create_glossary_panel() -> pn.Column:
    """클릭 가능한 용어 설명 패널 생성"""

    # 설명 표시 영역
    detail_area = pn.pane.Markdown(
        "*용어를 클릭하면 상세 설명이 여기에 표시됩니다.*",
        sizing_mode="stretch_width",
        styles={"background": "#f5f5f5", "padding": "12px", "border-radius": "4px", "min-height": "100px"}
    )

    # 용어 버튼들 생성
    buttons = []
    for key, info in GLOSSARY.items():
        btn = pn.widgets.Button(
            name=f"{info['term']}",
            button_type="light",
            width=150,
            height=35,
            styles={"font-size": "12px"}
        )

        # 클로저를 위해 기본값 인자 사용
        def make_callback(glossary_key):
            def callback(event):
                info = GLOSSARY[glossary_key]
                detail_area.object = f"### {info['term']}\n\n{info['detail']}"
            return callback

        btn.on_click(make_callback(key))
        buttons.append(btn)

    # 버튼들을 여러 행으로 배치
    button_rows = []
    for i in range(0, len(buttons), 5):
        button_rows.append(pn.Row(*buttons[i:i+5]))

    return pn.Column(
        pn.pane.Markdown("### 📖 용어 설명 (클릭하세요)"),
        *button_rows,
        pn.layout.Divider(),
        detail_area,
        sizing_mode="stretch_width",
    )


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

    # 용어 설명 패널 (접을 수 있는 Accordion)
    glossary_accordion = pn.Accordion(
        ("📖 용어 설명 (클릭하여 펼치기)", create_glossary_panel()),
        active=[],  # 기본적으로 접혀있음
        sizing_mode="stretch_width",
    )

    return pn.Column(
        pn.pane.Markdown("# AutoRAG 테스트 케이스 비교"),
        pn.pane.Markdown("두 테스트 케이스의 평가 결과를 나란히 비교합니다."),
        glossary_accordion,
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
