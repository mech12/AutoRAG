#!/usr/bin/env python3
"""테스트 케이스 설정 파일 파서"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TestCase:
    """테스트 케이스 설정"""

    name: str
    input_dir: str
    output_dir: str
    description: str = ""
    num_qa: int = 20
    use_llm: bool = False
    chunk_size: int = 512
    chunk_overlap: int = 50
    recursive: bool = False
    rag_config: str = "sample_config/rag/korean/non_gpu/simple_korean_custom.yaml"
    parse_config: str = ""  # 외부 parse config 파일 경로 (비어있으면 기본 pdfminer 사용)
    chunk_config: str = ""  # 외부 chunk config 파일 경로 (비어있으면 기본 Token 사용)
    env: dict = field(default_factory=dict)

    @property
    def data_dir(self) -> str:
        """데이터 출력 디렉토리"""
        return f"{self.output_dir}/data"

    @property
    def trial_dir(self) -> str:
        """평가 결과 디렉토리"""
        return f"{self.output_dir}/trial"


def get_config_path() -> str:
    """설정 파일 경로 반환 (scripts 폴더 기준)"""
    script_dir = Path(__file__).parent
    return str(script_dir / "test-config.yaml")


def load_config(config_path: Optional[str] = None) -> dict:
    """설정 파일 로드"""
    if config_path is None:
        config_path = get_config_path()
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_testcase(name: str, config_path: Optional[str] = None) -> TestCase:
    """테스트 케이스 로드"""
    config = load_config(config_path)
    defaults = config.get("defaults", {})
    case = config["test_cases"].get(name)

    if not case:
        available = list(config["test_cases"].keys())
        raise ValueError(
            f"테스트 케이스 '{name}'을 찾을 수 없습니다.\n"
            f"사용 가능한 케이스: {', '.join(available)}"
        )

    # defaults와 병합
    merged = {**defaults, **case, "name": name}

    # TestCase 필드만 추출
    valid_fields = {f for f in TestCase.__dataclass_fields__}
    filtered = {k: v for k, v in merged.items() if k in valid_fields}

    return TestCase(**filtered)


def list_testcases(config_path: Optional[str] = None) -> list[tuple[str, str]]:
    """모든 테스트 케이스 목록 (이름, 설명)"""
    config = load_config(config_path)
    return [
        (name, case.get("description", ""))
        for name, case in config["test_cases"].items()
    ]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 특정 테스트 케이스 정보 출력
        tc = load_testcase(sys.argv[1])
        print(f"Name: {tc.name}")
        print(f"Description: {tc.description}")
        print(f"Input: {tc.input_dir}")
        print(f"Output: {tc.output_dir}")
        print(f"Data dir: {tc.data_dir}")
        print(f"Trial dir: {tc.trial_dir}")
        print(f"Num QA: {tc.num_qa}")
        print(f"Use LLM: {tc.use_llm}")
        print(f"Chunk size: {tc.chunk_size}")
        print(f"Chunk overlap: {tc.chunk_overlap}")
        print(f"Parse config: {tc.parse_config or '(기본: pdfminer)'}")
        print(f"Chunk config: {tc.chunk_config or '(기본: Token)'}")
    else:
        # 테스트 케이스 목록 출력 (copy & paste 가능한 명령어 포함)
        print("=" * 60)
        print("사용 가능한 테스트 케이스")
        print("=" * 60)
        print()

        for name, desc in list_testcases():
            print(f"[{name}] {desc}")
            print(f"  make run-testcase TESTCASE={name}")
            print(f"  make prepare-data TESTCASE={name}")
            print(f"  make evaluate-custom TESTCASE={name}")
            print(f"  make show-testcase TESTCASE={name}")
            print()

        print("-" * 60)
        print("결과 비교: make compare-results")
        print("도움말:    make help-testcase")
