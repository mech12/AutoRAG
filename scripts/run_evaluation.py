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

# 한글-로마자 변환 테이블 (간단 버전)
KOREAN_TO_ROMAN = {
    "인사규정": "insa",
    "고압가스": "gas",
    "취업규칙": "rule",
    "전체": "all",
    "청크": "chunk",
    "상세": "detail",
}


def _make_safe_collection_name(name: str) -> str:
    """
    Milvus 컬렉션 이름으로 사용할 수 있도록 변환.
    - 한글은 미리 정의된 매핑 또는 해시로 변환
    - 특수문자는 언더스코어로 변환
    - 영문/숫자/언더스코어만 허용
    """
    import hashlib
    import re

    result = name

    # 알려진 한글 단어를 로마자로 변환
    for korean, roman in KOREAN_TO_ROMAN.items():
        result = result.replace(korean, roman)

    # 남은 한글이 있으면 해시로 변환
    if re.search(r"[가-힣]", result):
        # 한글 부분만 추출하여 해시
        korean_parts = re.findall(r"[가-힣]+", result)
        for korean in korean_parts:
            hash_val = hashlib.md5(korean.encode()).hexdigest()[:8]
            result = result.replace(korean, f"kr{hash_val}")

    # 특수문자를 언더스코어로 변환
    result = re.sub(r"[^a-zA-Z0-9_]", "_", result)

    # 연속 언더스코어 제거
    result = re.sub(r"_+", "_", result)

    # 앞뒤 언더스코어 제거
    result = result.strip("_")

    return result.lower()


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

    # Milvus 컬렉션 이름 동적 생성
    # MILVUS_COLLECTION_NAME_PREFIX가 설정되어 있으면 테스트케이스별 컬렉션 생성
    milvus_prefix = env.get("MILVUS_COLLECTION_NAME_PREFIX")
    if milvus_prefix and "MILVUS_COLLECTION_NAME" not in tc.env:
        # Milvus 컬렉션 이름: 영문, 숫자, 언더스코어만 허용
        # 한글 테스트케이스 이름을 안전한 이름으로 변환
        safe_name = _make_safe_collection_name(testcase)
        collection_name = f"{milvus_prefix}_autorag_{safe_name}"
        env["MILVUS_COLLECTION_NAME"] = collection_name
        print(f"  Milvus 컬렉션: {collection_name}")

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
