#!/usr/bin/env python3
"""테스트 케이스의 QA 데이터를 표시합니다."""

import sys
from pathlib import Path

import pandas as pd

# scripts 폴더의 testcase_config 모듈 import
sys.path.insert(0, str(Path(__file__).parent))
from testcase_config import load_testcase


def show_qa_data(testcase_name: str):
    """테스트 케이스의 QA 데이터를 표시합니다."""
    try:
        tc = load_testcase(testcase_name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    qa_path = Path(tc.data_dir) / "qa.parquet"
    corpus_path = Path(tc.data_dir) / "corpus.parquet"

    print()
    print("=" * 70)
    print(f"  테스트 케이스: {tc.name}")
    print(f"  설명: {tc.description}")
    print("=" * 70)
    print()

    # QA 데이터 확인
    if not qa_path.exists():
        print(f"  QA 데이터 없음: {qa_path}")
        print()
        print("  데이터를 먼저 준비하세요:")
        print(f"    make prepare-data TESTCASE={testcase_name}")
        print()
        sys.exit(1)

    # QA 데이터 로드
    qa_df = pd.read_parquet(qa_path)

    print(f"  데이터 경로: {tc.data_dir}")
    print(f"  QA 개수: {len(qa_df)}")
    print()

    # Corpus 정보
    if corpus_path.exists():
        corpus_df = pd.read_parquet(corpus_path)
        print(f"  Corpus 문서 수: {len(corpus_df)}")
        print()

    print("-" * 70)
    print("  질문 목록")
    print("-" * 70)
    print()

    for i, row in qa_df.iterrows():
        query = row["query"]
        # 질문이 너무 길면 줄여서 표시
        if len(query) > 100:
            query_display = query[:100] + "..."
        else:
            query_display = query

        print(f"  [{i+1}] {query_display}")

        # 정답 문서 ID 표시 (있으면)
        if "retrieval_gt" in row and row["retrieval_gt"]:
            gt = row["retrieval_gt"]
            if isinstance(gt, list) and len(gt) > 0:
                if isinstance(gt[0], list):
                    doc_ids = gt[0][:3]  # 첫 번째 그룹에서 최대 3개
                else:
                    doc_ids = gt[:3]
                print(f"      정답 문서: {doc_ids}")

        print()

    print("-" * 70)
    print()
    print("  상세 데이터 확인:")
    print(f"    python -c \"import pandas as pd; print(pd.read_parquet('{qa_path}').to_string())\"")
    print()
    print("  평가 실행:")
    print(f"    make evaluate-custom TESTCASE={testcase_name}")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python show_testcase.py <testcase_name>")
        print()
        print("Example:")
        print("  python show_testcase.py hr_rule_milvus")
        print("  make show-testcase TESTCASE=hr_rule_milvus")
        sys.exit(1)

    testcase_name = sys.argv[1]
    show_qa_data(testcase_name)


if __name__ == "__main__":
    main()
