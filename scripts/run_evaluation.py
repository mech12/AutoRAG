#!/usr/bin/env python3
"""
테스트 케이스 기반 RAG 평가 실행

사용법:
    python scripts/run_evaluation.py --testcase 인사규정
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from testcase_config import load_testcase

# Load environment variables
load_dotenv()


def run_evaluation(testcase: str):
    """테스트 케이스로 평가 실행"""
    tc = load_testcase(testcase)

    print("=" * 60)
    print(f"RAG 평가 실행: {tc.name}")
    print("=" * 60)
    print(f"  설명: {tc.description}")
    print(f"  데이터: {tc.data_dir}")
    print(f"  결과: {tc.trial_dir}")
    print(f"  설정: {tc.rag_config}")
    print()

    # Check data files exist
    qa_path = f"{tc.data_dir}/qa.parquet"
    corpus_path = f"{tc.data_dir}/corpus.parquet"

    if not os.path.exists(qa_path):
        print(f"Error: {qa_path} not found.")
        print(f"먼저 데이터를 준비하세요: make prepare-data TESTCASE={testcase}")
        sys.exit(1)

    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        print(f"먼저 데이터를 준비하세요: make prepare-data TESTCASE={testcase}")
        sys.exit(1)

    # 환경변수 오버라이드
    env = os.environ.copy()
    env.update(tc.env)

    # Build command
    cmd = [
        "autorag",
        "evaluate",
        "--config",
        tc.rag_config,
        "--qa_data_path",
        qa_path,
        "--corpus_data_path",
        corpus_path,
        "--project_dir",
        tc.trial_dir,
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, env=env, check=True)
        print()
        print("=" * 60)
        print("평가 완료!")
        print("=" * 60)
        print(f"\n결과 확인:")
        print(f"  cat {tc.trial_dir}/0/summary.csv")
        print(f"  make dashboard TRIAL_DIR={tc.trial_dir}/0")
    except subprocess.CalledProcessError as e:
        print(f"\n평가 실패: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run RAG evaluation for a test case")
    parser.add_argument(
        "--testcase",
        type=str,
        required=True,
        help="테스트 케이스 이름 (scripts/test-config.yaml에서 로드)",
    )

    args = parser.parse_args()
    run_evaluation(args.testcase)


if __name__ == "__main__":
    main()
