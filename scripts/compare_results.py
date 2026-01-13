#!/usr/bin/env python3
"""
테스트 케이스 결과 비교

사용법:
    python scripts/compare_results.py
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from testcase_config import list_testcases, load_testcase


def extract_metrics(trial_dir: str) -> dict:
    """trial 디렉토리에서 주요 메트릭 추출"""
    metrics = {}

    # Retrieval metrics
    retrieval_paths = [
        f"{trial_dir}/0/retrieve_node_line/semantic_retrieval/summary.csv",
        f"{trial_dir}/0/retrieve_node_line/lexical_retrieval/summary.csv",
    ]

    for retrieval_path in retrieval_paths:
        if os.path.exists(retrieval_path):
            try:
                ret_df = pd.read_csv(retrieval_path)
                if "retrieval_f1" in ret_df.columns:
                    metrics["retrieval_f1"] = ret_df["retrieval_f1"].iloc[0]
                if "retrieval_recall" in ret_df.columns:
                    metrics["retrieval_recall"] = ret_df["retrieval_recall"].iloc[0]
                if "retrieval_precision" in ret_df.columns:
                    metrics["retrieval_precision"] = ret_df["retrieval_precision"].iloc[
                        0
                    ]
                break
            except Exception:
                continue

    # Generator metrics
    gen_path = f"{trial_dir}/0/post_retrieve_node_line/generator/summary.csv"
    if os.path.exists(gen_path):
        try:
            gen_df = pd.read_csv(gen_path)
            if "rouge" in gen_df.columns:
                metrics["rouge"] = gen_df["rouge"].iloc[0]
            if "execution_time" in gen_df.columns:
                metrics["exec_time"] = gen_df["execution_time"].iloc[0]
        except Exception:
            pass

    return metrics


def compare_all():
    """모든 테스트 케이스 결과 비교"""
    results = []

    for name, desc in list_testcases():
        tc = load_testcase(name)
        summary_path = f"{tc.trial_dir}/0/summary.csv"

        if os.path.exists(summary_path):
            metrics = {"testcase": name, "description": desc[:30]}
            metrics.update(extract_metrics(tc.trial_dir))
            results.append(metrics)

    if results:
        df = pd.DataFrame(results)

        print()
        print("=" * 70)
        print("테스트 케이스 결과 비교")
        print("=" * 70)
        print()

        # Format numeric columns
        float_cols = ["retrieval_f1", "retrieval_recall", "retrieval_precision", "rouge"]
        for col in float_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "-")

        if "exec_time" in df.columns:
            df["exec_time"] = df["exec_time"].apply(
                lambda x: f"{x:.2f}s" if pd.notna(x) else "-"
            )

        # Print table
        try:
            print(df.to_markdown(index=False))
        except ImportError:
            # tabulate not installed, use simple format
            print(df.to_string(index=False))

        print()
        print("=" * 70)
    else:
        print()
        print("실행된 테스트 케이스가 없습니다.")
        print()
        print("테스트 케이스를 실행하려면:")
        print("  make run-testcase TESTCASE=<name>")
        print()
        print("사용 가능한 테스트 케이스:")
        for name, desc in list_testcases():
            print(f"  - {name}: {desc}")


def main():
    compare_all()


if __name__ == "__main__":
    main()
